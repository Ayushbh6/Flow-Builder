import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
import asyncio

from app.services.chatbot_service import ChatbotService


@patch('app.services.chatbot_service.OpenAI')
@patch('app.services.chatbot_service.AsyncOpenAI')
@patch('app.services.chatbot_service.Pinecone')
def test_chatbot_service_init(mock_pinecone, mock_async_openai, mock_openai):
    """Test ChatbotService initialization"""
    # Create the service
    service = ChatbotService()
    
    # Check that the clients were initialized
    assert mock_openai.called
    assert mock_async_openai.called
    assert mock_pinecone.called


@patch('app.services.chatbot_service.OpenAI')
def test_get_embedding(mock_openai):
    """Test the embedding generation functionality"""
    # Mock the embedding response
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Create mock response data
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.embedding = [0.1, 0.2, 0.3]
    mock_response.data = [mock_data]
    mock_client.embeddings.create.return_value = mock_response
    
    # Create the service and call the method
    service = ChatbotService()
    embedding = service.get_embedding("test query")
    
    # Verify the response
    assert embedding == [0.1, 0.2, 0.3]
    assert mock_client.embeddings.create.called


@patch('app.services.chatbot_service.OpenAI')
@patch('app.services.chatbot_service.Pinecone')
def test_vector_search(mock_pinecone, mock_openai):
    """Test vector search functionality"""
    # Mock OpenAI client
    mock_openai_client = MagicMock()
    mock_openai.return_value = mock_openai_client
    
    # Mock embedding response
    mock_embedding_response = MagicMock()
    mock_embedding_data = MagicMock()
    mock_embedding_data.embedding = [0.1, 0.2, 0.3]
    mock_embedding_response.data = [mock_embedding_data]
    mock_openai_client.embeddings.create.return_value = mock_embedding_response
    
    # Mock Pinecone client
    mock_pc = MagicMock()
    mock_pinecone.return_value = mock_pc
    mock_index = MagicMock()
    mock_pc.Index.return_value = mock_index
    
    # Mock query response
    mock_match = MagicMock()
    mock_match.id = "test_id"
    mock_match.score = 0.95
    mock_match.metadata = {
        "document_id": 1,
        "source_file": "test.pdf",
        "original_text": "This is the original text",
        "contextual_summary": "This is a contextual summary"
    }
    mock_query_response = MagicMock()
    mock_query_response.matches = [mock_match]
    mock_index.query.return_value = mock_query_response
    
    # Mock reranking
    mock_rerank_data = MagicMock()
    mock_rerank_data.score = 0.98
    mock_rerank_data.document = MagicMock()
    mock_rerank_data.document.text = "This is a contextual summary"
    mock_rerank_response = MagicMock()
    mock_rerank_response.data = [mock_rerank_data]
    mock_pc.inference.rerank.return_value = mock_rerank_response
    
    # Create the service and call vector search
    service = ChatbotService()
    result = service.vector_search("test query")
    
    # Check that the embedding was generated
    assert mock_openai_client.embeddings.create.called
    
    # Check that Pinecone was queried
    assert mock_index.query.called
    
    # Check that reranking was performed
    assert mock_pc.inference.rerank.called
    
    # Check that the result is not empty
    assert result
    assert "test.pdf" in result


@pytest.mark.asyncio
@patch('app.services.chatbot_service.OpenAI')
@patch('app.services.chatbot_service.AsyncOpenAI')
async def test_process_chat(mock_async_openai, mock_openai):
    """Test the chatbot's process_chat method"""
    # Mock synchronous client for tool calls
    mock_sync_client = MagicMock()
    mock_openai.return_value = mock_sync_client
    
    # Mock the tool call response
    mock_tool_call = MagicMock()
    mock_tool_call.type = "function_call"
    mock_tool_call.name = "retrieve_knowledge"
    mock_tool_call.call_id = "test_call_id"
    mock_tool_call.arguments = json.dumps({"query": "test query"})
    
    # Mock the response output
    mock_response = MagicMock()
    mock_response.output = [mock_tool_call]
    mock_response.output_text = "Test response"
    mock_sync_client.responses.create.return_value = mock_response
    
    # Mock the async client for streaming
    mock_async_client = AsyncMock()
    mock_async_openai.return_value = mock_async_client
    
    # Set up the streaming response
    mock_event1 = AsyncMock()
    mock_event1.type = "response.output_text.delta"
    mock_event1.delta = "Hello"
    
    mock_event2 = AsyncMock()
    mock_event2.type = "response.output_text.delta"
    mock_event2.delta = " world"
    
    # Create an async iterable for the streaming response
    class MockAsyncIterator:
        def __init__(self, items):
            self.items = items
            
        def __aiter__(self):
            return self
            
        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)
    
    mock_stream = MockAsyncIterator([mock_event1, mock_event2])
    mock_async_client.responses.create.return_value = mock_stream
    
    # Mock vector_search method
    with patch.object(ChatbotService, 'vector_search', return_value="Test search results"):
        # Create the service
        service = ChatbotService()
        
        # Call the method with test data
        history = [{"user": "previous question", "assistant": "previous answer"}]
        chunks = []
        
        # Collect the streaming chunks
        async for chunk in service.process_chat(history, "new question"):
            chunks.append(chunk)
        
        # Verify the result
        assert chunks == ["Hello", " world"]
        assert mock_sync_client.responses.create.called
        assert mock_async_client.responses.create.called


@patch('app.services.chatbot_service.OpenAI')
def test_chat(mock_openai):
    """Test the chatbot's non-streaming chat method"""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Set up response with no function call
    mock_response = MagicMock()
    mock_response.output = []
    mock_response.output_text = "Test response with no function call"
    
    # Set up response with function call
    mock_func_call = MagicMock()
    mock_func_call.type = "function_call"
    mock_func_call.name = "retrieve_knowledge"
    mock_func_call.call_id = "test_call_id"
    mock_func_call.arguments = json.dumps({"query": "test query"})
    
    mock_func_response = MagicMock()
    mock_func_response.output = [mock_func_call]
    mock_func_response.output_text = "Test function call response"
    
    # Make the first call return a function call, and the second call return no function call
    mock_client.responses.create.side_effect = [mock_func_response, mock_response]
    
    # Mock vector_search method
    with patch.object(ChatbotService, 'vector_search', return_value="Test search results"):
        # Create the service
        service = ChatbotService()
        
        # Call the method with test data
        history = [{"user": "previous question", "assistant": "previous answer"}]
        result = service.chat(history, "new question")
        
        # Verify the result
        assert result == "Test response with no function call"
        assert mock_client.responses.create.call_count == 2  # Two calls made


@patch('app.services.chatbot_service.OpenAI')
def test_create_rag_tools(mock_openai):
    """Test the RAG tools creation"""
    # Create the service
    service = ChatbotService()
    
    # Get the tools
    tools = service.create_rag_tools()
    
    # Verify the tools format
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert tools[0]["name"] == "retrieve_knowledge"
    assert "parameters" in tools[0]
    assert "query" in tools[0]["parameters"]["properties"] 