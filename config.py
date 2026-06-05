import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Groq Model — free, fast
    # Options: llama3-8b-8192 | llama3-70b-8192 | mixtral-8x7b-32768 | gemma2-9b-it
    # GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")

    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Embedding — free, no API key needed
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Chunking
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 200

    # Retrieval
    TOP_K_RESULTS: int = 6

    # Flask
    FLASK_HOST: str = "0.0.0.0"
    FLASK_PORT: int = 5000
    SECRET_KEY: str = "documind-groq-secret"

    # Paths
    UPLOAD_FOLDER: str = "uploads"
    FAISS_INDEX_PATH: str = "faiss_index"
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "txt", "md"}
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50MB

config = Config()
