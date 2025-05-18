import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.flow import Flow
from app.schemas.flow import FlowCreate, FlowUpdate, FlowInDB

# Configure logging
logger = logging.getLogger(__name__)

def get_flows(db: Session, skip: int = 0, limit: int = 100) -> List[Flow]:
    """
    Get a list of flows with pagination
    """
    return db.query(Flow).filter(Flow.is_active == True).offset(skip).limit(limit).all()

def get_flow_by_id(db: Session, flow_id: int) -> Optional[Flow]:
    """
    Get a flow by its ID
    """
    return db.query(Flow).filter(Flow.id == flow_id, Flow.is_active == True).first()

def create_flow(db: Session, flow_data: FlowCreate) -> Flow:
    """
    Create a new flow
    """
    # Create the new flow
    db_flow = Flow(
        name=flow_data.name,
        description=flow_data.description,
        flow_data=flow_data.flow_data
    )
    
    # Save to the database
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    
    return db_flow

def update_flow(db: Session, flow_id: int, flow_data: FlowUpdate) -> Optional[Flow]:
    """
    Update an existing flow
    """
    # Get the flow
    db_flow = get_flow_by_id(db, flow_id)
    if not db_flow:
        return None
    
    # Update fields
    update_data = flow_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_flow, key, value)
    
    # Save changes
    db.commit()
    db.refresh(db_flow)
    
    return db_flow

def delete_flow(db: Session, flow_id: int) -> bool:
    """
    Soft delete a flow (set is_active to False)
    """
    db_flow = get_flow_by_id(db, flow_id)
    if not db_flow:
        return False
    
    # Soft delete
    db_flow.is_active = False
    db.commit()
    
    return True

def validate_flow_config(flow_data: Dict[str, Any]) -> bool:
    """
    Validate flow configuration
    
    This is a basic validation that checks for required fields.
    More complex validation would be implemented here.
    """
    # Check for required fields in flow configuration
    if not isinstance(flow_data, dict):
        return False
    
    # Check for nodes array
    if "nodes" not in flow_data or not isinstance(flow_data["nodes"], list):
        return False
    
    # Check for edges array
    if "edges" not in flow_data or not isinstance(flow_data["edges"], list):
        return False
    
    # Basic validation of each node
    for node in flow_data["nodes"]:
        if "id" not in node or "type" not in node:
            return False
    
    # Basic validation of each edge
    for edge in flow_data["edges"]:
        if "id" not in edge or "source" not in edge or "target" not in edge:
            return False
    
    return True 