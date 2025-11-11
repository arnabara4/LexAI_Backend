import os
import datetime
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_TLS = str(os.environ.get('MAIL_USE_TLS', 'False')).lower() in ['true', 'on', '1']
    MAIL_USE_SSL = str(os.environ.get('MAIL_USE_SSL', 'True')).lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'a-different-secret-key-for-jwt'
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_BLOCKLIST_ENABLED = True
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=30)
    
    # --- Standardized on GEMINI_API_KEY ---
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    EMBEDDING_MODEL_NAME = 'models/embedding-001'
    VECTOR_COLLECTION_NAME = 'legal_india_v1' 
    
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    

class DevelopmentConfig(Config):
    """
    Development-specific configuration.
    """
    DEBUG = True
    
    JWT_REFRESH_COOKIE_SECURE = False
    JWT_REFRESH_COOKIE_SAMESITE = "Lax"

    # --- Warnings ---
    if not os.environ.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL is not set. App will use a default, which might fail.")
    if not os.environ.get('MAIL_USERNAME'):
        print("WARNING: MAIL_USERNAME is not set. Email sending will fail.")
    if not os.environ.get('GEMINI_API_KEY'):
        print("WARNING: GEMINI_API_KEY is not set. RAG and Chat will fail.")

class ProductionConfig(Config):
    """
    Production-specific configuration.
    """
    DEBUG = False
    
    JWT_REFRESH_COOKIE_SECURE = True
    JWT_REFRESH_COOKIE_SAMESITE = "None"
    
    # --- Crash if secrets are missing ---
    if not os.environ.get('DATABASE_URL'):
        raise RuntimeError("FATAL: DATABASE_URL environment variable is not set for production.")
    if not os.environ.get('MAIL_USERNAME') or not os.environ.get('MAIL_PASSWORD'):
        raise RuntimeError("FATAL: Email credentials are not set for production.")
    
    # --- ⬇️ THIS IS THE FIX ⬇️ ---
    if not os.environ.get('GEMINI_API_KEY'):
        raise RuntimeError("FATAL: GEMINI_API_KEY is not set for production.")
    # --- ⬆️ END OF FIX ⬆️ ---

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}