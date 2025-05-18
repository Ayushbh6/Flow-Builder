import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
import json

from app.models.flow import Flow
from app.services.flow_execution_service import FlowExecutionService
from app.services.chatbot_service import ChatbotService
from app.schemas.flow import FlowCreate

@pytest.fixture
def flow_execution_service():
    """Flow execution service fixture"""
    return FlowExecutionService()

def test_validate_connections_valid(flow_execution_service):
    """Test validation of a valid flow configuration"""
    # Valid flow with input -> transform -> output
    valid_flow = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input", "input_key": "question"}},
            {"id": "2", "type": "transform", "data": {"label": "Transform"}},
            {"id": "3", "type": "output", "data": {"label": "Output", "output_key": "answer"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"},
            {"id": "e2-3", "source": "2", "target": "3"}
        ]
    }
    
    is_valid, error = flow_execution_service.validate_connections(valid_flow)
    
    assert is_valid is True
    assert error == ""
    
def test_validate_connections_missing_fields(flow_execution_service):
    """Test validation of a flow with missing required fields"""
    # Flow missing edges
    invalid_flow = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ]
    }
    
    is_valid, error = flow_execution_service.validate_connections(invalid_flow)
    
    assert is_valid is False
    assert "must include 'nodes' and 'edges'" in error
    
def test_validate_connections_invalid_edge(flow_execution_service):
    """Test validation of a flow with invalid edge connections"""
    # Flow with edge to nonexistent node
    invalid_flow = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ],
        "edges": [
            {"id": "e1-3", "source": "1", "target": "3"}  # Node 3 doesn't exist
        ]
    }
    
    is_valid, error = flow_execution_service.validate_connections(invalid_flow)
    
    assert is_valid is False
    assert "does not exist" in error
    
def test_validate_connections_disconnected_nodes(flow_execution_service):
    """Test validation of a flow with disconnected nodes"""
    # Flow with disconnected input node
    invalid_flow = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ],
        "edges": []  # No connections
    }
    
    is_valid, error = flow_execution_service.validate_connections(invalid_flow)
    
    assert is_valid is False
    assert "no outgoing connections" in error
    
def test_validate_connections_cycle(flow_execution_service):
    """Test validation of a flow with a cycle"""
    # Flow with a cycle
    invalid_flow = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "transform", "data": {"label": "Transform 1"}},
            {"id": "3", "type": "transform", "data": {"label": "Transform 2"}},
            {"id": "4", "type": "output", "data": {"label": "Output"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"},
            {"id": "e2-3", "source": "2", "target": "3"},
            {"id": "e3-2", "source": "3", "target": "2"},  # Creates cycle between 2 and 3
            {"id": "e3-4", "source": "3", "target": "4"}
        ]
    }
    
    is_valid, error = flow_execution_service.validate_connections(invalid_flow)
    
    assert is_valid is False
    assert "cycles" in error.lower()

@pytest.mark.asyncio
async def test_execute_flow_simple(db: Session):
    """Test executing a simple flow"""
    # Create mock chatbot service
    mock_chatbot = MagicMock(spec=ChatbotService)
    mock_chatbot.chat.return_value = "Mocked chatbot response"
    
    # Create service with mocked chatbot
    flow_execution_service = FlowExecutionService(chatbot_service=mock_chatbot)
    
    # Create a test flow
    flow_data = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input", "input_key": "question"}},
            {"id": "2", "type": "chatbot", "data": {"label": "Chatbot"}},
            {"id": "3", "type": "output", "data": {"label": "Output", "output_key": "answer"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"},
            {"id": "e2-3", "source": "2", "target": "3"}
        ]
    }
    
    # Create a flow in the database
    db_flow = Flow(
        name="Test Execution Flow",
        description="A flow for testing execution",
        flow_data=flow_data
    )
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    
    # Input data for the flow
    input_data = {"question": "What is the meaning of life?"}
    
    # Execute the flow
    result = await flow_execution_service.execute_flow(db_flow.id, input_data, db)
    
    # Verify the results
    assert "answer" in result
    assert result["answer"] == "Mocked chatbot response"
    
    # Verify chatbot service was called with the input
    mock_chatbot.chat.assert_called_once_with([], "What is the meaning of life?")

@pytest.mark.asyncio
async def test_execute_flow_nonexistent(flow_execution_service, db: Session):
    """Test executing a nonexistent flow"""
    with pytest.raises(ValueError) as excinfo:
        await flow_execution_service.execute_flow(9999, {"input": "test"}, db)
    
    assert "not found" in str(excinfo.value) 