import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# --- Configuration ---
DB_PERSIST_DIRECTORY = "./constitution_db"

# --- Load API Key ---
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY not found in .env file.")
    exit()

def view_database_contents(db_directory):
    """Loads a persistent ChromaDB and prints its contents."""
    print(f"Loading database from: {db_directory}")
    
    try:
        # 1. Initialize the embedding model (must be the same as when you created the DB)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # 2. Load the persistent database
        db = Chroma(persist_directory=db_directory, embedding_function=embeddings)
        
        # 3. Retrieve all documents
        # The .get() method retrieves documents and their metadata
        retrieved_data = db.get()
        
        all_documents = retrieved_data['documents']
        all_metadata = retrieved_data['metadatas']
        
        print(f"\n--- Database contains {len(all_documents)} entries. ---\n")
        
        # 4. Print each entry
        for i, (metadata, document) in enumerate(zip(all_metadata, all_documents)):
            print(f"--- Entry {i+1} ---")
            print(f"Metadata: {metadata}")
            # Print the first 150 characters of the document content for brevity
            print(f"Content: {document[:150]}...")
            print("-" * 20 + "\n")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the database directory exists and is not corrupted.")

# --- Run the script ---
if __name__ == "__main__":
    view_database_contents(DB_PERSIST_DIRECTORY)