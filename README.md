# ⚖️ LexAI: Backend API

This repository contains the complete backend server for LexAI, an AI-powered legal document analyzer designed for India.

This server is a modular Flask application that provides a secure authentication system, a powerful RAG (Retrieval-Augmented Generation) pipeline for document analysis, and a conversational chat API.

---

## Backend Features

* **Secure Authentication:** Full user signup, login, and email verification flow.
* **Cookie-Based Sessions:** Uses `Flask-JWT-Extended` with `HttpOnly` refresh token cookies (and a `jti` allowlist) for a secure, professional auth flow.
* **Hybrid AI Pipeline:**
    * **Analysis:** Uses a high-accuracy API model (`gpt-4o` or `gemini-1.5-pro`) for in-depth RAG analysis.
    * **Chat:** Uses a fast, local model (`phi3:mini` via Ollama) for lag-free conversational follow-ups.
* **Private RAG:** Embeddings are generated locally using `bge-m3`, so user documents are *never* sent to a third-party API for embedding.
* **Smart Ingestion:**
    * **Hierarchical Chunking:** Intelligently splits legal acts based on their structure (`CHAPTER`, `Section`, `(1)`, `(a)`) for maximum relevance.
    * **OCR Support:** Automatically reads text from both digital and "photo-type" scanned PDFs using `pypdf` and `pytesseract`.
* **Database Architecture:**
    * **Auth DB:** Uses **Supabase** (Cloud Postgres) for all critical user and token tables.
    * **Vector DB:** Uses **ChromaDB** (local folder) for zero-latency RAG queries.

---

## 🛠 Tech Stack

* **Framework:** Flask
* **Auth Database:** PostgreSQL (on Supabase)
* **ORM:** Flask-SQLAlchemy
* **Auth Logic:** Flask-JWT-Extended, Flask-Bcrypt
* **Email:** Flask-Mail (with Gmail)
* **Vector Database:** ChromaDB (Local)
* **Embedding Model:** `bge-m3` (via `sentence-transformers`)
* **Analysis LLM:** `gpt-4o` (via `langchain-openai`) or `gemini-1.5-pro` (via `langchain-google-genai`)
* **Chat LLM:** `phi3:mini` (via `Ollama` and `langchain-ollama`)
* **PDF Parsing:** `pypdf`, `pytesseract`, `pdf2image`

---

## 🚀 Local Setup & Running

Follow these steps to get the backend running on your local machine (like your Mac).

### 1. Prerequisites

Before you begin, you must have the following installed on your system:
* Python 3.10+
* **Ollama:** Download from [ollama.com](https://ollama.com/)
* **Tesseract & Poppler** (for OCR): `brew install tesseract poppler`

### 2. Install AI Models

Your AI pipeline runs two local models. You need to pull them.

1.  **Pull the Chat Model (phi3:mini):**
    ```bash
    ollama pull phi3:mini
    ```
2.  **Pre-download the Embedding Model (bge-m3):**
    * Activate your virtual environment (see Step 3).
    * Run this command to download the model files (this will take a few minutes):
        ```bash
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
        ```

### 3. Install Python Dependencies

1.  **Clone the Repo:**
    ```bash
    git clone [your-repo-url]
    cd backend
    ```
2.  **Create & Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install All Libraries:**
    ```bash
    pip install -r requirements.txt
    ```

### 4. Set Up Databases

1.  **Auth Database (Supabase):**
    * Create a free project on [Supabase.com](https://supabase.com).
    * Go to **Settings > Database** and copy your `psql` **Connection string**.
    * Go to the **SQL Editor** in Supabase.
    * Copy the *entire* SQL script from `setup_supabase_auth.sql` (or the script I provided) and run it to create all your `core` and `auth` tables.

2.  **Vector Database (ChromaDB):**
    * Place all your legal act PDFs into the `backend/data/All_Acts_PDFs/` folder.
    * Run the ingestion script to build your `chroma_db` folder:
        ```bash
        python data/ingest.py
        ```

### 5. Configure Your Secrets (`.env`)

1.  Create a file named `.env` in the `backend/` folder.
2.  Copy the contents of `.env.example` (if you have one) or use the template below.
3.  Fill in *all* the secret keys.

    ```ini
    # Set to 'development' for local running
    FLASK_CONFIG=development

    # Your Supabase connection string
    DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres"

    # Your frontend URL (for CORS)
    FRONTEND_URL="http://localhost:5173"

    # Generate with 'python -c "import secrets; print(secrets.token_hex(32))"'
    SECRET_KEY="your_strong_random_flask_key"
    JWT_SECRET_KEY="your_DIFFERENT_strong_random_jwt_key"

    # Your API key for the "Analyzer" LLM (Gemini or OpenAI)
    GEMINI_API_KEY="your_google_ai_studio_key"
    OPENAI_API_KEY="your_openai_api_key"

    # Your Google App Password for sending emails
    MAIL_SERVER=smtp.googlemail.com
    MAIL_PORT=465
    MAIL_USE_TLS=False
    MAIL_USE_SSL=True
    MAIL_USERNAME="your-email@gmail.com"
    MAIL_PASSWORD="your-16-character-app-password"
    ```

### 6. Run the Application

You are now ready to run the server.

```bash
# Set the FLASK_APP environment variable
export FLASK_APP=run.py

# Run the Flask app
flask run
