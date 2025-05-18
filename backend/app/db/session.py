from typing import Generator
from .base import SessionLocal

def get_db() -> Generator:
    """
    Get a database session
    
    Returns:
        Generator: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 