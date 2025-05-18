import pytest
from sqlalchemy.orm import Session

from app.models.flow import Flow
from app.schemas.flow import FlowCreate, FlowUpdate
from app.services import flow_service

def test_flow_config_validation():
    """Test flow configuration validation"""
    # Valid flow configuration
    valid_flow = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"}
        ]
    }
    
    assert flow_service.validate_flow_config(valid_flow) is True
    
    # Invalid flow - no nodes
    invalid_flow_1 = {
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"}
        ]
    }
    
    assert flow_service.validate_flow_config(invalid_flow_1) is False
    
    # Invalid flow - no edges
    invalid_flow_2 = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ]
    }
    
    assert flow_service.validate_flow_config(invalid_flow_2) is False
    
    # Invalid flow - invalid node structure
    invalid_flow_3 = {
        "nodes": [
            {"id": "1", "data": {"label": "Input"}},  # Missing type
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"}
        ]
    }
    
    assert flow_service.validate_flow_config(invalid_flow_3) is False
    
    # Invalid flow - invalid edge structure
    invalid_flow_4 = {
        "nodes": [
            {"id": "1", "type": "input", "data": {"label": "Input"}},
            {"id": "2", "type": "output", "data": {"label": "Output"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1"}  # Missing target
        ]
    }
    
    assert flow_service.validate_flow_config(invalid_flow_4) is False

def test_create_flow(db: Session):
    """Test creating a flow"""
    # Create a test flow data
    flow_data = FlowCreate(
        name="Test Flow",
        description="A test flow",
        flow_data={
            "nodes": [
                {"id": "1", "type": "input", "data": {"label": "Input"}},
                {"id": "2", "type": "output", "data": {"label": "Output"}}
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"}
            ]
        }
    )
    
    # Create the flow
    db_flow = flow_service.create_flow(db, flow_data)
    
    # Verify created flow
    assert db_flow.id is not None
    assert db_flow.name == "Test Flow"
    assert db_flow.description == "A test flow"
    assert db_flow.is_active is True
    assert db_flow.flow_data == flow_data.flow_data

def test_get_flow(db: Session):
    """Test getting a flow by ID"""
    # Create a test flow
    flow_data = FlowCreate(
        name="Test Flow 2",
        description="Another test flow",
        flow_data={
            "nodes": [
                {"id": "1", "type": "input", "data": {"label": "Input"}},
                {"id": "2", "type": "output", "data": {"label": "Output"}}
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"}
            ]
        }
    )
    
    # Create the flow
    db_flow = flow_service.create_flow(db, flow_data)
    
    # Get the flow
    retrieved_flow = flow_service.get_flow_by_id(db, db_flow.id)
    
    # Verify retrieved flow
    assert retrieved_flow is not None
    assert retrieved_flow.id == db_flow.id
    assert retrieved_flow.name == "Test Flow 2"
    
    # Try to get a nonexistent flow
    nonexistent_flow = flow_service.get_flow_by_id(db, 9999)
    assert nonexistent_flow is None

def test_update_flow(db: Session):
    """Test updating a flow"""
    # Create a test flow
    flow_data = FlowCreate(
        name="Flow to Update",
        description="Flow that will be updated",
        flow_data={
            "nodes": [
                {"id": "1", "type": "input", "data": {"label": "Input"}},
                {"id": "2", "type": "output", "data": {"label": "Output"}}
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"}
            ]
        }
    )
    
    # Create the flow
    db_flow = flow_service.create_flow(db, flow_data)
    
    # Update data
    update_data = FlowUpdate(
        name="Updated Flow",
        description="This flow has been updated"
    )
    
    # Update the flow
    updated_flow = flow_service.update_flow(db, db_flow.id, update_data)
    
    # Verify the update
    assert updated_flow is not None
    assert updated_flow.id == db_flow.id
    assert updated_flow.name == "Updated Flow"
    assert updated_flow.description == "This flow has been updated"
    
    # The flow_data should remain unchanged
    assert updated_flow.flow_data == db_flow.flow_data
    
    # Try to update a nonexistent flow
    nonexistent_update = flow_service.update_flow(db, 9999, update_data)
    assert nonexistent_update is None

def test_delete_flow(db: Session):
    """Test deleting a flow"""
    # Create a test flow
    flow_data = FlowCreate(
        name="Flow to Delete",
        description="Flow that will be deleted",
        flow_data={
            "nodes": [
                {"id": "1", "type": "input", "data": {"label": "Input"}},
                {"id": "2", "type": "output", "data": {"label": "Output"}}
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"}
            ]
        }
    )
    
    # Create the flow
    db_flow = flow_service.create_flow(db, flow_data)
    
    # Delete the flow
    result = flow_service.delete_flow(db, db_flow.id)
    
    # Verify deletion
    assert result is True
    
    # Verify the flow is soft deleted
    deleted_flow = db.query(Flow).filter(Flow.id == db_flow.id).first()
    assert deleted_flow is not None
    assert deleted_flow.is_active is False
    
    # Verify get_flow_by_id doesn't return it
    assert flow_service.get_flow_by_id(db, db_flow.id) is None
    
    # Try to delete a nonexistent flow
    nonexistent_delete = flow_service.delete_flow(db, 9999)
    assert nonexistent_delete is False 