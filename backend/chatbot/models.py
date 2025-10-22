"""
Pydantic models for the Green Agent chatbot.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    USER = "user"
    WHITE_AGENT = "white_agent"
    GREEN_AGENT = "green_agent"

class MessageType(str, Enum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    content: str
    agent_type: AgentType = AgentType.USER
    timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    status: str = "pending"  # pending, success, error

class ChatResponse(BaseModel):
    message: str
    agent_type: AgentType
    tool_calls: List[ToolCall] = []
    status: str = "success"
    timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AgentStatus(BaseModel):
    is_active: bool
    current_agent: AgentType
    conversation_length: int
    last_activity: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    class_type: str = "economy"

class FlightSearchResponse(BaseModel):
    flights: List[Dict[str, Any]]
    total_results: int
    search_params: Dict[str, Any]
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
