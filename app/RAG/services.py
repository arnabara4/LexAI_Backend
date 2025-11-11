import pypdf
from werkzeug.datastructures import FileStorage
from app.auth.models import User
from app.extensions import db

import pytesseract
from pdf2image import convert_from_bytes

from . import rag_service
from . import llm_service

def extract_text_from_upload(pdf_file: FileStorage) -> str:
    """
    Extracts text from an uploaded PDF file (FileStorage).
    Tries fast digital extraction first, then falls back to OCR.
    """
    print("  - Reading (digital) from user upload...")
    try:
        # Reset stream for pypdf
        pdf_file.seek(0)
        reader = pypdf.PdfReader(pdf_file)
        
        if reader.is_encrypted:
            raise ValueError("The uploaded PDF is password-protected.")

        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n\n"
        
        if full_text and len(full_text.strip()) > 100: # 100 chars is enough
            print("  - Digital text extracted from upload.")
            return full_text
            
    except Exception as e:
        print(f"  - Digital extraction failed: {e}. Trying OCR.")

    # --- FALLBACK TO OCR ---
    print(f"  - Digital text not found. Starting OCR on user upload...")
    try:
        pdf_file.seek(0)
        
        images = convert_from_bytes(pdf_file.read())
    
        full_ocr_text = ""
        for img in images:
            full_ocr_text += pytesseract.image_to_string(img) + "\n\n"
            
        if not full_ocr_text.strip():
            raise ValueError("OCR failed. PDF may be empty or unreadable.")

        print(f"  - OCR text extracted from upload.")
        return full_ocr_text
        
    except Exception as e:
        print(f"  - OCR extraction FAILED for user upload: {e}")
        raise ValueError(f"Could not read the provided PDF file. {str(e)}")

def perform_legal_analysis(document_text: str, user_id: str) -> str:
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")
        
    print(f"Analysis requested by user: {user.email}")
    
    print("Step 1: Finding relevant context...")
    retrieved_context = rag_service.retrieve(document_text)
    print("Step 2: Generating analysis...")
    analysis_json_string = llm_service.llm_analysis(
        context=retrieved_context,
        user_document=document_text
    )
    
    print("Analysis complete.")
    
    return analysis_json_string