import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "FlowBot Builder"
    API_V1_STR: str = "/api"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./flowbot.db")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend with frontend
    ]
    
    # LlamaParse settings
    LLAMA_CLOUD_API_KEY: Optional[str] = os.getenv("LLAMA_CLOUD_API_KEY")
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSION: int = 1536  # Dimension for text-embedding-3-small
    SUMMARY_MODEL: str = os.getenv("SUMMARY_MODEL", "gpt-4.1-mini")
    COMPLETION_MODEL: str = os.getenv("COMPLETION_MODEL", "gpt-4.1")
    
    # Pinecone settings
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "flowbot-kb")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "default")
    
    # File upload settings
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    
    class Config:
        case_sensitive = True


settings = Settings() 