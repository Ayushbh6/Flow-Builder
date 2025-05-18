from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base

class Document(Base):
    """Document model representing an uploaded document"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)  # Path to the stored file
    file_type = Column(String)  # e.g., "pdf", "docx"
    original_size = Column(Integer)  # File size in bytes
    content_text = Column(Text, nullable=True)  # Extracted text content
    content_format = Column(String, default="markdown")  # Format of extracted text: markdown or plaintext
    # Status values: uploaded, processing, processed, indexing, indexed, error
    status = Column(String, default="uploaded")
    error_message = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 