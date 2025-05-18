from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.services.flow_execution_service import FlowExecutionService
from app.models.flow import Flow

router = APIRouter()
flow_execution_service = FlowExecutionService()

@router.post("/{flow_id}/execute")
async def execute_flow(
    flow_id: int,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Execute a flow with the given input data
    """
    try:
        # Check if flow exists
        flow = db.query(Flow).filter(Flow.id == flow_id, Flow.is_active == True).first()
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Execute the flow
        result = await flow_execution_service.execute_flow(flow_id, input_data, db)
        
        return {
            "flow_id": flow_id,
            "flow_name": flow.name,
            "result": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing flow: {str(e)}")

@router.get("/{flow_id}/validate")
def validate_flow(
    flow_id: int,
    db: Session = Depends(get_db)
):
    """
    Validate a flow's configuration
    """
    try:
        # Check if flow exists
        flow = db.query(Flow).filter(Flow.id == flow_id, Flow.is_active == True).first()
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Validate connections
        is_valid, error = flow_execution_service.validate_connections(flow.flow_data)
        
        if is_valid:
            return {"flow_id": flow_id, "valid": True}
        else:
            return {"flow_id": flow_id, "valid": False, "error": error}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating flow: {str(e)}") 