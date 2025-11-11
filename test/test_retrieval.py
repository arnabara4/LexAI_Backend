# in backend/test/test_rag.py

import chromadb
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path # <-- 1. Import the 'pathlib' library

# --- 2. THE "SMART PATH" FIX ---
# This line gets the path to this *exact file* (test_rag.py)
SCRIPT_DIR = Path(__file__).resolve().parent

# This line goes "up" one level to find the 'backend/' root
BACKEND_ROOT = SCRIPT_DIR.parent 

# This line builds a 100% reliable, absolute path to your database
CHROMA_PATH = BACKEND_ROOT / "chroma_db"
# --- END FIX ---

COLLECTION_NAME = "legal_india_bge_m3"
EMBEDDING_MODEL_NAME = 'BAAI/bge-m3'
TEST_QUERY = "What is the punishment for organised crime in public examinations?"

def run_test():
    print("--- RAG Database Test ---")
    print(f"Looking for database at: {CHROMA_PATH}") # Debug line

    # --- 3. LOAD THE MODEL ---
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    print("Model loaded successfully.")

    # --- 4. CONNECT TO CHROMADB ---
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH)) # Use str(CHROMA_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        print(f"Did you run 'python data/ingest.py' first?")
        return
    
    db_count = collection.count()
    print(f"\nSuccessfully connected to collection: '{COLLECTION_NAME}'")
    print(f"Total Chunks in Database: {db_count}")
    
    if db_count == 0:
        print("ERROR: Your database is empty. Please run 'python data/ingest.py'.")
        return

    # ... (rest of your test script is identical) ...
    # --- 5. RUN THE TEST QUERY ---
    print(f"\n--- Testing with query ---")
    print(f"Query: \"{TEST_QUERY}\"")
    
    query_embedding = model.encode(TEST_QUERY, normalize_embeddings=True)
    
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=3
    )
    
    # --- 6. SHOW THE RESULTS ---
    print("\n--- Top 3 Results from RAG ---")
    
    if not results['documents']:
        print("No results found.")
        return

    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n--- Result #{i+1} ---")
        print(f"Source: {meta['source']}")
        print("Text:")
        print("..." + doc.strip().replace("\n", " ")[:500] + "...")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    run_test()