import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import tempfile
from unittest.mock import patch
from app.models.document import Document

def test_upload_document(client: TestClient, db: Session):
    """Test document upload endpoint"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_file.write(b"This is a test document for the API test")
        temp_file_path = temp_file.name
    
    try:
        # Open the file for upload
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/api/documents/",
                files={"file": ("test_document.txt", f, "text/plain")}
            )
        
        # Check response
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_document.txt"
        assert data["file_type"] == "txt"
        assert data["status"] == "uploaded"
        
        # Check if document was created in the database
        document_id = data["id"]
        document = db.query(Document).filter(Document.id == document_id).first()
        assert document is not None
        assert document.filename == "test_document.txt"
        
        # Test get document by ID
        response = client.get(f"/api/documents/{document_id}")
        assert response.status_code == 200
        assert response.json()["id"] == document_id
        
        # Test list documents
        response = client.get("/api/documents/")
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 1
        assert any(doc["id"] == document_id for doc in documents)
        
        # Test delete document
        response = client.delete(f"/api/documents/{document_id}")
        assert response.status_code == 200
        
        # Verify document was deleted
        response = client.get(f"/api/documents/{document_id}")
        assert response.status_code == 404
        
    finally:
        # Clean up: remove the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@patch('app.services.document_service.LlamaParse')
def test_upload_pdf_document(mock_llama_parse, client: TestClient, db: Session):
    """Test PDF document upload and processing with mocked LlamaParse"""
    # Mock LlamaParse behavior
    mock_llama_instance = mock_llama_parse.return_value
    
    # Create a temporary PDF test file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"%PDF-1.4\nTest PDF content")  # Simple PDF-like content
        temp_file_path = temp_file.name
    
    try:
        # Open the file for upload
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/api/documents/",
                files={"file": ("test_document.pdf", f, "application/pdf")}
            )
        
        # Check response
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_document.pdf"
        assert data["file_type"] == "pdf"
        assert data["status"] == "uploaded"
        assert data.get("content_format") == "markdown"
        
        # We don't test actual processing since it's a background task and we've mocked LlamaParse
    finally:
        # Clean up: remove the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def test_upload_invalid_file_type(client: TestClient):
    """Test uploading an invalid file type"""
    # Create a temporary test file with invalid extension
    with tempfile.NamedTemporaryFile(suffix=".invalid", delete=False) as temp_file:
        temp_file.write(b"This is an invalid file type")
        temp_file_path = temp_file.name
    
    try:
        # Open the file for upload
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/api/documents/",
                files={"file": ("test_document.invalid", f, "application/octet-stream")}
            )
        
        # Check response - should be a bad request
        assert response.status_code == 400
        
    finally:
        # Clean up: remove the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def test_get_nonexistent_document(client: TestClient):
    """Test getting a document that doesn't exist"""
    # Use a very high ID that shouldn't exist
    response = client.get("/api/documents/99999")
    assert response.status_code == 404 