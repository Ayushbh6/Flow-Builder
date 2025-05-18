from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class FlowBase(BaseModel):
    """Base schema for flow data"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    flow_data: Dict[str, Any] = Field(...)


class FlowCreate(FlowBase):
    """Schema for creating a new flow"""
    pass


class FlowUpdate(BaseModel):
    """Schema for updating an existing flow"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    flow_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FlowInDB(FlowBase):
    """Schema for flow data as stored in the database"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FlowList(BaseModel):
    """Schema for returning a list of flows"""
    flows: List[FlowInDB]
    total: int 