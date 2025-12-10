"""Trace ledger for recording all tool calls."""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..models.trace_models import ToolCallTrace, TraceLedger
from ..infrastructure.controller import GreenAgentController
from ..streaming.event_queue import get_event_queue
from ..utils.df_parser import extract_df_operations


class TraceLedgerManager:
    """Manages append-only trace ledger."""
    
    def __init__(self, controller: GreenAgentController):
        """
        Initialize trace ledger manager.
        
        Args:
            controller: Green Agent controller for run ID and hashing
        """
        self.controller = controller
        self.ledger: Optional[TraceLedger] = None
        self._traces: List[ToolCallTrace] = []
        self.event_queue = get_event_queue()
    
    def initialize(self, run_id: Optional[str] = None):
        """Initialize new trace ledger for a run."""
        if run_id is None:
            run_id = self.controller.start_run()
        
        self.ledger = TraceLedger(
            run_id=run_id,
            created_at=datetime.now(),
            traces=[]
        )
        self._traces = []
    
    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        return_value: Any,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None,
        tool_input: Optional[str] = None  # For extracting DataFrame operations from python_repl_ast
    ):
        """
        Record a tool call in the ledger.
        
        Args:
            tool_name: Name of the tool called
            arguments: Tool call arguments
            return_value: Return value from tool
            execution_time_ms: Execution time in milliseconds
            error: Error message if call failed
            tool_input: Raw tool input (for parsing DataFrame operations)
        """
        if self.ledger is None:
            self.initialize()
        
        # Extract DataFrame operations if this is a python_repl_ast call
        df_operations = None
        if tool_name == 'python_repl_ast' and tool_input:
            try:
                df_operations = extract_df_operations(tool_input)
            except Exception as e:
                print(f"Failed to extract DataFrame operations: {e}")
                df_operations = None
        
        # Compute return value hash
        return_value_hash = None
        if return_value is not None:
            try:
                if isinstance(return_value, str):
                    hash_input = return_value
                else:
                    hash_input = json.dumps(return_value, sort_keys=True, default=str)
                return_value_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
            except Exception:
                return_value_hash = str(hash(return_value))[:16]
        
        # Get run hash from controller
        run_id = self.controller.get_run_id()
        run_hash = self.controller.get_run_hash()
        
        trace = ToolCallTrace(
            timestamp=datetime.now(),
            run_id=run_id or "unknown",
            tool_name=tool_name,
            arguments=arguments,
            return_value=return_value,
            return_value_hash=return_value_hash,
            execution_time_ms=execution_time_ms,
            error=error,
            df_operations=df_operations
        )
        
        self._traces.append(trace)
        if self.ledger:
            self.ledger.traces.append(trace)
        
        # Emit trace update event (sync-safe via queue)
        try:
            event = {
                'type': 'trace_update',
                'timestamp': trace.timestamp.isoformat(),
                'data': {
                    'tool_name': trace.tool_name,
                    'arguments': trace.arguments,
                    'return_value': trace.return_value,
                    'return_value_hash': trace.return_value_hash,
                    'timestamp': trace.timestamp.isoformat(),
                    'execution_time_ms': trace.execution_time_ms,
                    'error': trace.error,
                    'df_operations': trace.df_operations
                }
            }
            self.event_queue.put(event)
        except Exception as e:
            print(f"Failed to queue trace update: {e}")
    
    def get_traces(self) -> List[ToolCallTrace]:
        """Get all traces."""
        return self._traces.copy()
    
    def get_ledger(self) -> Optional[TraceLedger]:
        """Get the complete ledger."""
        if self.ledger:
            self.ledger.traces = self._traces.copy()
        return self.ledger
    
    def export_to_json(self, file_path: Optional[str] = None) -> str:
        """
        Export ledger to JSON.
        
        Args:
            file_path: Optional file path to save to
            
        Returns:
            JSON string representation
        """
        ledger = self.get_ledger()
        if ledger is None:
            return json.dumps({"error": "No ledger initialized"})
        
        # Convert to dict with proper serialization
        ledger_dict = ledger.model_dump(mode='json')
        json_str = json.dumps(ledger_dict, indent=2, default=str)
        
        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def clear(self):
        """Clear ledger (for new run)."""
        self.ledger = None
        self._traces = []

