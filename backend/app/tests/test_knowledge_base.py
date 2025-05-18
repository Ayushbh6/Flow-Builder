import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import tempfile
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.document import Document
from app.services.knowledge_service import chunk_markdown, index_document
from app.core.config import settings


def test_chunk_markdown():
    """Test markdown chunking functionality"""
    # Create a very large text that will definitely exceed the token limit
    test_text = "# Heading\n\n" + "Sample text. " * 10000  # Much larger text
    
    # Test with default settings
    chunks = chunk_markdown(test_text)
    assert len(chunks) > 1  # Should split into multiple chunks
    
    # Test with smaller token limit to ensure we get more chunks
    small_chunks = chunk_markdown(test_text, max_tokens=1000, overlap=100)
    assert len(small_chunks) > len(chunks)  # Should create more, smaller chunks
    
    # Check overlap if we have multiple chunks
    if len(chunks) > 1:
        # Get the last part of the first chunk
        first_chunk_end = chunks[0][-100:]
        # Check if it appears at the beginning of the second chunk
        assert first_chunk_end in chunks[1]


@pytest.mark.asyncio
@patch('app.services.knowledge_service.AsyncOpenAI')
@patch('app.services.knowledge_service.Pinecone')
@patch('app.services.knowledge_service.prepare_document_chunks')
async def test_index_document(mock_prepare_document, mock_pinecone, mock_openai, db: Session):
    """Test document indexing functionality by mocking the prepare_document_chunks function"""
    # Create a test document
    test_doc = Document(
        filename="test_doc.txt",
        file_path="/tmp/test_doc.txt",
        file_type="txt",
        original_size=1000,
        content_text="# Test Document\n\nThis is a test document for indexing.\n\n" + "Test content. " * 100,
        status="processed"
    )
    db.add(test_doc)
    db.commit()
    db.refresh(test_doc)
    
    # Mock the prepare_document_chunks function to just update the document status
    async def mock_success(*args, **kwargs):
        # Get the document from the first argument (document_id)
        document_id = args[0]
        document = db.query(Document).filter(Document.id == document_id).first()
        document.status = "indexed"
        db.commit()
    
    # Set the mock implementation
    mock_prepare_document.side_effect = mock_success
    
    # Run the indexing function
    await index_document(test_doc.id, db)
    
    # Verify the function was called
    assert mock_prepare_document.called
    
    # Verify the document status is updated
    db.refresh(test_doc)
    assert test_doc.status == "indexed"


@pytest.mark.asyncio
@patch('app.services.knowledge_service.AsyncOpenAI')
@patch('app.services.knowledge_service.Pinecone')
@patch('app.services.knowledge_service.prepare_document_chunks')
async def test_index_document_error_handling(mock_prepare_document, mock_pinecone, mock_openai, db: Session):
    """Test error handling during document indexing"""
    # Create a test document
    test_doc = Document(
        filename="test_error_doc.txt",
        file_path="/tmp/test_error_doc.txt",
        file_type="txt",
        original_size=1000,
        content_text="# Test Document\n\nThis is a test document for error handling.",
        status="processed"
    )
    db.add(test_doc)
    db.commit()
    db.refresh(test_doc)
    
    # Mock the prepare_document_chunks function to raise an exception
    mock_prepare_document.side_effect = Exception("Test error")
    
    # Run the indexing function
    await index_document(test_doc.id, db)
    
    # Verify the document status is updated to error
    db.refresh(test_doc)
    assert test_doc.status == "error"
    assert test_doc.error_message is not None
    assert "Test error" in test_doc.error_message 