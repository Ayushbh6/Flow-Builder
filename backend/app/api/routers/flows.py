from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.flow import Flow
from app.schemas.flow import FlowCreate, FlowUpdate, FlowInDB, FlowList
from app.services import flow_service

router = APIRouter()

@router.get("/", response_model=FlowList)
def get_flows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all flows with pagination
    """
    flows = flow_service.get_flows(db, skip=skip, limit=limit)
    total = db.query(Flow).filter(Flow.is_active == True).count()
    
    return {"flows": flows, "total": total}

@router.get("/{flow_id}", response_model=FlowInDB)
def get_flow(flow_id: int, db: Session = Depends(get_db)):
    """
    Get a flow by ID
    """
    flow = flow_service.get_flow_by_id(db, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return flow

@router.post("/", response_model=FlowInDB)
def create_flow(flow_data: FlowCreate, db: Session = Depends(get_db)):
    """
    Create a new flow
    """
    # Validate flow configuration
    if not flow_service.validate_flow_config(flow_data.flow_data):
        raise HTTPException(status_code=400, detail="Invalid flow configuration")
    
    # Create the flow
    flow = flow_service.create_flow(db, flow_data)
    
    return flow

@router.put("/{flow_id}", response_model=FlowInDB)
def update_flow(flow_id: int, flow_data: FlowUpdate, db: Session = Depends(get_db)):
    """
    Update an existing flow
    """
    # Validate flow configuration if provided
    if flow_data.flow_data and not flow_service.validate_flow_config(flow_data.flow_data):
        raise HTTPException(status_code=400, detail="Invalid flow configuration")
    
    # Update the flow
    updated_flow = flow_service.update_flow(db, flow_id, flow_data)
    if not updated_flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return updated_flow

@router.delete("/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db)):
    """
    Delete a flow (soft delete - set is_active to False)
    """
    success = flow_service.delete_flow(db, flow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return {"message": f"Flow {flow_id} has been deleted"} 