import os
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPT_DIR.parent.parent
CHROMA_PATH = BACKEND_ROOT/"chroma_db"

COLLECTION_NAME = "legal_india_bge_m3"
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
LLM_MODEL = "gemini-2.5-pro"


try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME,device = "cpu")
    print("Succesfully imported embdding model")
except Exception as e:
    embedding_model = None
    print(f"Error in importing embedding model: {e}")

try:
    db = chromadb.PersistentClient(path = str(CHROMA_PATH))
    collection = db.get_collection(name = COLLECTION_NAME)
    print("Successfully conencted to Chromadb")
except Exception as e:
    print(f"Error in connecting to vector db: {e}")


def retrieve(query: str):
    try:
        query_embedding = embedding_model.encode(query,normalize_embeddings = True)

        results = collection.query(
        query_embeddings = [query_embedding.tolist()],
        n_results = 3
        )
    except Exception as e:
        print(f"Error in retrieval: {e}")
    
    return results




