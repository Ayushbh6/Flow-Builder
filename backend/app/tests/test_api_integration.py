import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from app.models.document import Document
from app.core.config import settings


def test_knowledge_base_status_endpoint(client: TestClient, db: Session):
    """Test the knowledge base status endpoint"""
    # Add some documents with different statuses
    docs = [
        Document(
            filename="test1.pdf",
            file_path="/tmp/test1.pdf",
            file_type="pdf",
            original_size=1000,
            status="uploaded"
        ),
        Document(
            filename="test2.pdf", 
            file_path="/tmp/test2.pdf",
            file_type="pdf",
            original_size=1000,
            status="processed"
        ),
        Document(
            filename="test3.pdf",
            file_path="/tmp/test3.pdf",
            file_type="pdf",
            original_size=1000,
            status="indexed"
        ),
        Document(
            filename="test4.pdf",
            file_path="/tmp/test4.pdf",
            file_type="pdf",
            original_size=1000,
            status="indexing"
        ),
    ]
    for doc in docs:
        db.add(doc)
    db.commit()
    
    # Call the endpoint
    response = client.get("/api/knowledge-bases/status")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "total_documents" in data
    assert "indexed_documents" in data
    assert "processing_documents" in data
    assert "pinecone_configured" in data
    assert "openai_configured" in data
    assert "ready" in data
    
    # Check counts
    assert data["total_documents"] == 4
    assert data["indexed_documents"] == 1
    assert data["processing_documents"] == 1


@patch('app.api.routers.knowledge_bases.index_document')
def test_index_document_endpoint(mock_index_document, client: TestClient, db: Session):
    """Test the index document endpoint"""
    # Create a test document
    doc = Document(
        filename="index_test.pdf",
        file_path="/tmp/index_test.pdf",
        file_type="pdf",
        original_size=1000,
        status="processed",
        content_text="This is a test document for indexing."
    )
    db.add(doc)
    db.commit()
    
    # Call the endpoint
    response = client.post(f"/api/knowledge-bases/{doc.id}/index")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "indexing"
    
    # Check that the document status was updated in the database
    db.refresh(doc)
    assert doc.status == "indexing"
    
    # Check that the background task was added
    assert mock_index_document.called


def test_index_nonexistent_document(client: TestClient):
    """Test indexing a nonexistent document"""
    # Use a very high ID that shouldn't exist
    response = client.post("/api/knowledge-bases/99999/index")
    assert response.status_code == 404


def test_index_document_without_content(client: TestClient, db: Session):
    """Test indexing a document without content"""
    # Create a test document without content
    doc = Document(
        filename="no_content.pdf",
        file_path="/tmp/no_content.pdf",
        file_type="pdf",
        original_size=1000,
        status="processed",
        content_text=None
    )
    db.add(doc)
    db.commit()
    
    # Call the endpoint
    response = client.post(f"/api/knowledge-bases/{doc.id}/index")
    
    # Check the response
    assert response.status_code == 400


@patch('app.api.routers.chatbot.ChatbotService')
def test_chatbot_status_endpoint(mock_chatbot_service, client: TestClient):
    """Test the chatbot status endpoint"""
    # Call the endpoint
    response = client.get("/api/chatbots/status")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "openai_configured" in data
    assert "pinecone_configured" in data
    assert "ready" in data


@patch('app.api.routers.chatbot.chatbot_service', new_callable=MagicMock)
def test_chat_endpoint(mock_chatbot_service, client: TestClient):
    """Test the chat endpoint"""
    # Mock the chatbot service
    mock_chatbot_service.chat.return_value = "This is a test response"
    
    # Prepare the request data
    request_data = {
        "message": "Test question",
        "history": [
            {"user": "Previous question", "assistant": "Previous answer"}
        ]
    }
    
    # Call the endpoint
    response = client.post("/api/chatbots/chat", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "This is a test response"
    
    # Check that the chatbot service was called with the right parameters
    mock_chatbot_service.chat.assert_called_once()
    args, kwargs = mock_chatbot_service.chat.call_args
    assert args[0] == request_data["history"]
    assert args[1] == request_data["message"]


@patch('app.api.routers.chatbot.chatbot_service', new_callable=MagicMock)
def test_chat_stream_endpoint(mock_chatbot_service, client: TestClient):
    """Test the streaming chat endpoint"""
    # Mock the chatbot service process_chat method to return an async generator
    async def mock_process_chat(*args, **kwargs):
        yield "Test response chunk"
    
    mock_chatbot_service.process_chat.return_value = mock_process_chat()
    
    # Prepare the request data
    request_data = {
        "message": "Test streaming question",
        "history": []
    }
    
    # Call the endpoint
    response = client.post("/api/chatbots/chat/stream", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    # Check that the chatbot service was called
    mock_chatbot_service.process_chat.assert_called_once()


def test_chat_without_message(client: TestClient):
    """Test the chat endpoint without a message"""
    # Prepare the request data without a message
    request_data = {
        "history": []
    }
    
    # Call the endpoint
    response = client.post("/api/chatbots/chat", json=request_data)
    
    # Check the response
    assert response.status_code == 400 