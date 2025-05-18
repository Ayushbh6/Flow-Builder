from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.models.document import Document
from app.services.knowledge_service import index_document
from app.core.config import settings

router = APIRouter()

@router.get("/")
def get_knowledge_bases():
    """
    Get all knowledge bases
    """
    # To be implemented
    return {"message": "Get all knowledge bases - to be implemented"}

@router.get("/status")
def get_knowledge_base_status(db: Session = Depends(get_db)):
    """
    Get the status of the knowledge base
    """
    document_count = db.query(Document).count()
    indexed_count = db.query(Document).filter(Document.status == "indexed").count()
    processing_count = db.query(Document).filter(Document.status == "indexing").count()
    
    status = {
        "total_documents": document_count,
        "indexed_documents": indexed_count,
        "processing_documents": processing_count,
        "pinecone_configured": bool(settings.PINECONE_API_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "ready": bool(settings.PINECONE_API_KEY and settings.OPENAI_API_KEY)
    }
    
    return status

@router.post("/{document_id}/index")
async def index_document_endpoint(
    document_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger indexing of a document
    """
    # Check if document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if document has content
    if not document.content_text:
        raise HTTPException(status_code=400, detail="Document has no content to index")
    
    # Check configuration
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    if not settings.PINECONE_API_KEY:
        raise HTTPException(status_code=500, detail="Pinecone API key not configured")
    
    # Update status to indexing
    document.status = "indexing"
    db.commit()
    
    # Start indexing in background
    background_tasks.add_task(index_document, document_id, db)
    
    return {"message": f"Started indexing document {document_id}", "status": "indexing"} 