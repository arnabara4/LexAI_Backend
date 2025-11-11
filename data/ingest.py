import os
import chromadb
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer
from pathlib import Path

print("Loading environment variables...")
load_dotenv()

# --- 1. CONFIGURATION ---
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "legal_india_bge_m3"
PDF_SOURCE_DIR = "data/All_Acts_PDFs"

# Load the local model (runs once)
print("Loading bge-m3 model... (This may take a moment)")
EMBEDDING_MODEL = SentenceTransformer('BAAI/bge-m3', device='cpu')
print("Model loaded.")

def main():
    print("--- Starting Intelligent Ingestion Process ---")
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # --- 2. THE "HIERARCHICAL CHUNKER" UPGRADE ---
    # This is the new, "smart" splitter based on your uploaded PDFs.
    # It respects the legal document structure.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,  # Increased size to try and keep full sections
        chunk_overlap=200, # Overlap to maintain context between chunks
        
        # This is the HIERARCHY of separators, from most important to least.
        separators=[
            r"\nCHAPTER [IVXLCDM]+\n", # "CHAPTER I", "CHAPTER II"
            r"\n\d{1,3}\.\s",          # "1. ", "2. ", "10. ", "13A. "
            r"\n\(\d{1,2}\)\s",        # "(1) ", "(2) ", "(10) "
            r"\n\([a-z]\)\s",          # "(a) ", "(b) "
            "\n\n",                    # Paragraphs
            "\n",                      # Lines
            " "                        # Words
        ],
        is_separator_regex=True, # We are using regex in our separators
    )
    # --- END OF UPGRADE ---
    
    pdf_dir = Path(PDF_SOURCE_DIR)
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in directory: {PDF_SOURCE_DIR}")
        return

    print(f"Found {len(pdf_files)} PDF files to process.")
    
    total_chunks_processed = 0

    for pdf_file in pdf_files:
        print(f"\n--- Processing: {pdf_file.name} ---")
        
        try:
            loader = PyPDFLoader(str(pdf_file))
            pages = loader.load_and_split(text_splitter)
            
            if not pages:
                print(f"No text extracted from {pdf_file.name}. Skipping.")
                continue

            print(f"Split into {len(pages)} semantic chunks.")
            
            texts = [chunk.page_content for chunk in pages]
            
            # Add the source filename as metadata (critical for citations)
            metadatas = [
                {
                    # Get just the filename (e.g., "197504.pdf")
                    "source": Path(chunk.metadata.get('source', str(pdf_file.name))).name,
                    "page": chunk.metadata.get('page', 0)
                } 
                for chunk in pages
            ]
            
            # Create unique IDs
            ids = [f"{pdf_file.name}_chunk_{i}" for i in range(len(pages))]
            
            # Generate embeddings
            print(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = EMBEDDING_MODEL.encode(texts, normalize_embeddings=True)
            
            # Add to ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Successfully processed and stored {pdf_file.name}.")
            total_chunks_processed += len(pages)

        except Exception as e:
            # This ensures one corrupt PDF doesn't stop the whole process
            print(f"!!!!!!!! FAILED to process {pdf_file.name}: {e} !!!!!")
            print("Skipping this file.")

    print("\n--- Ingestion Complete ---")
    print(f"Total chunks processed: {total_chunks_processed}")
    print(f"Data stored in collection: {COLLECTION_NAME}")
    print(f"Vector Database setup is now COMPLETE.")

if __name__ == "__main__":
    main()