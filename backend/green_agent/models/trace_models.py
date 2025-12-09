"""Models for trace ledger entries."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class ToolCallTrace(BaseModel):
    """Single tool call trace entry."""
    timestamp: datetime
    run_id: str
    tool_name: str
    arguments: Dict[str, Any]
    return_value: Any
    return_value_hash: Optional[str] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None
    df_operations: Optional[List[Dict[str, Any]]] = None  # DataFrame operations extracted from python_repl_ast
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TraceLedger(BaseModel):
    """Complete trace ledger for a run."""
    run_id: str
    created_at: datetime
    traces: list[ToolCallTrace] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

