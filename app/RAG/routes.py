from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
import time, threading, json
from datetime import datetime

from . import RAG_bp, r
from .models import RAGSchema, ChatSchema
from .services import perform_legal_analysis, extract_text_from_upload
from .llm_service import llm_chat

# === GLOBAL RATE LIMIT CONTROL ===
MAX_CALLS_PER_MIN = 2
INTERVAL = 60 / MAX_CALLS_PER_MIN
last_call_time = 0
lock = threading.Lock()

def wait_for_slot():
    """Ensures we don’t exceed the Gemini free-tier limit."""
    global last_call_time
    with lock:
        now = time.time()
        elapsed = now - last_call_time
        if elapsed < INTERVAL:
            wait_time = INTERVAL - elapsed
            print(f"[RateLimiter] Sleeping {wait_time:.2f}s to respect quota...")
            time.sleep(wait_time)
        last_call_time = time.time()


# === Helper functions for Redis ===

def get_user_cache(user_id):
    key = f"lex:user:{user_id}"
    data = r.get(key)
    if data:
        return json.loads(data)
    # Default structure
    return {"chat_history": [], "analysis_result": None, "document_text": None, "timestamp": None}


def update_user_cache(user_id, cache_data):
    key = f"lex:user:{user_id}"
    cache_data["timestamp"] = datetime.now().timestamp()
    r.set(key, json.dumps(cache_data))
    r.expire(key, 86400)  # 24-hour expiry


# --- MAIN RAG ANALYSIS ENDPOINT ---
@RAG_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_document():
    """Hybrid endpoint: can analyze either uploaded PDF or pasted text."""
    try:
        current_user_id = get_jwt_identity()
        user_cache = get_user_cache(current_user_id)
        document_text = None

        # --- 1️⃣ Input parsing ---
        if 'document' in request.files:
            file = request.files['document']
            if not file or file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            if file.content_type != 'application/pdf':
                return jsonify({"error": "Invalid file type. Upload a PDF."}), 400
            document_text = extract_text_from_upload(file)
        elif request.is_json:
            data = request.get_json()
            try:
                validated_data = RAGSchema(**data)
                document_text = validated_data.text
            except ValidationError as e:
                return jsonify({"error": "Invalid text input", "details": e.errors()}), 422
        else:
            return jsonify({"error": "No document text or PDF file provided."}), 400

        # --- 2️⃣ Check Redis Cache ---
        if user_cache.get("document_text") == document_text and user_cache.get("analysis_result"):
            print("[Analyze] Returning cached analysis result.")
            return jsonify(user_cache["analysis_result"]), 200

        # --- 3️⃣ Apply rate limiting BEFORE LLM call ---
        wait_for_slot()

        # --- 4️⃣ Perform legal analysis ---
        analysis_result = perform_legal_analysis(
            document_text=document_text,
            user_id=current_user_id
        )

        if isinstance(analysis_result, str):
            try:
                analysis_result = json.loads(analysis_result)
            except json.JSONDecodeError:
                analysis_result = {"summary": "Error decoding analysis", "raw": analysis_result}

        # --- 5️⃣ Cache result ---
        user_cache["document_text"] = document_text
        user_cache["analysis_result"] = analysis_result
        update_user_cache(current_user_id, user_cache)

        print("[Analyze] Completed successfully (cached).")
        return jsonify(analysis_result), 200

    except ValueError as e:
        print(f"[Analyze] ValueError: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[Analyze] UNEXPECTED ERROR:\n{e}")
        return jsonify({"error": "An internal error occurred during analysis."}), 500


# --- FOLLOW-UP CHAT ENDPOINT ---
@RAG_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_document():
    """Handles chat interactions after analysis."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        validated_data = ChatSchema(**data)

        wait_for_slot()

        # --- Get and update chat history ---
        user_cache = get_user_cache(current_user_id)
        chat_history = validated_data.dict().get('history', [])
        doc_context = None

        # If analysis already exists, pass its summary or context to LLM
        if user_cache.get("analysis_result"):
            doc_context = json.dumps(user_cache["analysis_result"])

        # Call your LLM
        ai_response_text = llm_chat(
            history=chat_history,
            user_document=doc_context
        )

        # Append to cached chat
        chat_history.append({"role": "model", "content": ai_response_text})
        user_cache["chat_history"] = chat_history
        update_user_cache(current_user_id, user_cache)

        return jsonify({"role": "model", "content": ai_response_text}), 200

    except ValidationError as e:
        return jsonify({"error": "Invalid chat history", "details": e.errors()}), 422
    except Exception as e:
        print(f"[Chat] UNEXPECTED ERROR:\n{e}")
        return jsonify({"error": "An internal error occurred."}), 500

@RAG_bp.route('/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Fetch user's cached chat and analysis from Redis."""
    try:
        current_user_id = get_jwt_identity()
        user_cache = get_user_cache(current_user_id)
        
        return jsonify({
            "chat_history": user_cache.get("chat_history", []),
            "analysis_result": user_cache.get("analysis_result"),
            "document_text": user_cache.get("document_text")
        }), 200

    except Exception as e:
        print(f"[Chat History] ERROR: {e}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

@RAG_bp.route('/analyze/last', methods=['GET'])
@jwt_required()
def get_last_analysis():
    """Fetch the user's last analyzed document and result from cache."""
    try:
        current_user_id = get_jwt_identity()
        user_cache = get_user_cache(current_user_id)

        if not user_cache.get("analysis_result"):
            return jsonify({"message": "No cached analysis found."}), 404

        return jsonify({
            "document_text": user_cache.get("document_text"),
            "analysis_result": user_cache.get("analysis_result"),
            "timestamp": user_cache.get("timestamp")
        }), 200

    except Exception as e:
        print(f"[Get Analysis] ERROR: {e}")
        return jsonify({"error": "Failed to fetch previous analysis"}), 500
