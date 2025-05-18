from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    """Base schema for document data"""
    filename: str
    file_type: str

class DocumentCreate(DocumentBase):
    """Schema for creating a document (used internally)"""
    file_path: str
    original_size: int
    
class DocumentResponse(DocumentBase):
    """
    Schema for document response
    
    Status values:
    - uploaded: Document uploaded but not processed
    - processing: Text extraction in progress
    - processed: Text extraction complete
    - indexing: Document being indexed in knowledge base
    - indexed: Document successfully indexed in knowledge base
    - error: Processing or indexing failed
    """
    id: int
    status: str
    created_at: datetime
    text_preview: Optional[str] = None
    original_size: Optional[int] = None
    error_message: Optional[str] = None
    content_format: Optional[str] = "markdown"  # Format of the extracted text: markdown or plaintext
    
    class Config:
        orm_mode = True
        
class DocumentPreview(BaseModel):
    """Schema for document preview"""
    id: int
    filename: str
    file_type: str
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True 