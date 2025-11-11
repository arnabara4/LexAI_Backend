import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json

SYSTEM_PROMPT = """You are Lex AI an intelligent assistant specialized in interpreting Indian legal documents for laypeople. You are **not a lawyer**, and you must **never** provide legal advice or definitive interpretations of law.

---

## 🎯 ROLE AND PURPOSE
Your sole function is to **analyze the user-provided document** (such as a rental agreement, employment contract, sale deed, or other legal text) **using the supporting legal context** retrieved from the vector database.  
You must use this context to **explain, summarize, and highlight potential risks or confusing clauses** in **plain, everyday English**.

Your goal is **clarity and accessibility**, not legal precision. Avoid jargon, citations, or references to specific legal codes unless absolutely necessary for understanding.

---

## 🧠 TASK
Given:
1. A user-uploaded document (the text to analyze), and  
2. Additional retrieved legal context (from ChromaDB),  

you must produce a structured JSON response containing:
- a simplified summary of the document, and  
- specific clauses that may pose potential issues or need extra attention, each paired with a short plain-language explanation.

You must **only** use the provided context and document text. Do **not** invent, assume, or extrapolate from outside knowledge.

---

## 📦 OUTPUT FORMAT
You must respond **only** with a single, valid, raw JSON object — **no extra commentary, markdown, or text**.

The JSON must strictly follow this structure:

```json
{
  "summary": "A clear, simple-language explanation of what this document means and its main terms.",
  "red_flags": [
    {
      "clause": "Exact or near-exact text of the clause from the document.",
      "concern": "A short, plain-language explanation of why this clause might be confusing, risky, or important."
    }
  ]
}
"""

ANALYSIS_PROMPT_TEMPLATE = """
Here is the legal context I retrieved from my knowledge base:
--- BEGIN LEGAL CONTEXT ---
{context}
--- END LEGAL CONTEXT ---

Here is the user's document you must analyze:
--- BEGIN USER DOCUMENT ---
{document}
--- END USER DOCUMENT ---

Please analyze the user's document based *only* on the provided context and your core instructions.

Your response must be a single JSON object with this exact structure:
{{
  "summary": "A concise, plain-language summary of the user's document. Identify the key parties, their main responsibilities, and any significant financial obligations.",
  "red_flags": [
    {{
      "clause_text": "The exact, verbatim text of the clause from the user's document that is a potential red flag.",
      "concern": "A simple, 1-2 sentence explanation of *why* this is a concern for the user. (e.g., 'This clause allows for an automatic renewal without notice.')",
      "context_source": "The 'source' filename from the legal context that supports this concern (e.g., 'A2024-01.pdf'). If not supported by specific context, state 'General Concern'."
    }}
  ]
}}
"""

CHAT_SYSTEM_PROMPT = """
You are "Lex", an AI legal assistant and legal information specialist.
Your role is to help users understand the content and implications of legal documents
in a factual, neutral, and educational manner.

GUIDELINES:
- Provide **accurate, verifiable information** about laws, legal terms, and procedures.
- When explaining, focus on **clarity, simplicity, and correctness**.
- You may summarize what a legal concept or clause generally means,
  or what it typically implies in a legal context.
- **NEVER** offer legal advice or guidance about what the user should do.
  (e.g., never say "You should file a case" or "You can sue them.")
- If the question requires **interpretation, opinion, or personal recommendation**, 
  politely refuse and remind the user that you can only provide factual or educational explanations.
- **Stay on topic.** If the user asks something unrelated to law or the document, politely decline.

TONE AND STYLE:
- Be professional yet conversational and approachable.
- Use plain language; avoid excessive jargon.
- When relevant, reference the **general legal framework** (e.g., Indian Contract Act, 1872),
  but avoid making jurisdiction-specific claims unless clear from context.

Your goal: 
Help users clearly understand *what* a legal term, clause, or section means — 
not *what they should do about it*.
"""
llm_analyzer = None
llm_chatter = None

try:
    # --- 4. THIS IS THE FIX FOR YOUR QUOTA ERROR ---
    llm_analyzer = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",  # Use the powerful Gemini 1.5 Pro
        google_api_key=os.environ.get('GEMINI_API_KEY'),
        convert_system_message_to_human=True, # Helps with System Prompts
        response_mime_type='application/json' # Ask for JSON directly
    )
    print("Google Gemini 1.5 Pro (Analyzer) model loaded.")
    # --- END FIX ---
except Exception as e:
    print(f"CRITICAL: Error setting up Gemini 2.5 Pro:{e}")


try:
    llm_chatter = ChatOllama(model="phi3:mini")
    # --- END OF LAG FIX ---
    print("Ollama Phi-3 Mini (Chatter) model loaded.")
except Exception as e:
    print(f"CRITICAL: Failed to initialize Ollama: {e}")
    print("Is the Ollama app running on your Mac?")


# --- 6. ANALYSIS FUNCTION (Bugs Fixed) ---
def llm_analysis(context: str, user_document: str) -> str:
    """
    Calls the HIGH-ACCURACY model (GPT-4o) for the main analysis.
    """
    # --- 7. FIXED: Check for 'llm_analyzer' ---
    if not llm_analyzer:
        raise Exception("LLM service (Analyzer) not initalised properly")
    
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        context = context,
        document = user_document
    )

    messages = [
        SystemMessage(content = SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]

    print("Sending prompt to GPT-4o analyzer...")
    response = llm_analyzer.invoke(messages)

    # response.content is the raw JSON string
    return response.content

# --- 8. CHAT FUNCTION (Bugs Fixed) ---
def llm_chat(history: list, user_document: str) -> str:
    """
    Calls the FAST, LOCAL model (Llama 3) for the follow-up chat.
    """
    if not llm_chatter:
        raise Exception("LLM service (Chatter) not initalised properly")

    messages = [
        SystemMessage(content=CHAT_SYSTEM_PROMPT),
        HumanMessage(content=f"Here is the original document we are discussing: <document>{user_document}</document>")
    ]
    
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "").strip()
        if not content:
            continue

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role in ["model", "assistant"]:
            # --- 9. FIXED: 'messages.append' ---
            messages.append(AIMessage(content=content))
     
    print(f"Sending chat history to local Llama 3 chatter...")
    # --- 10. FIXED: 'llm.invoke(messages)' ---
    response = llm_chatter.invoke(messages)

    return response.content