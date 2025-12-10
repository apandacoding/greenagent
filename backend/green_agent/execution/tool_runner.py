"""Deterministic tool runner for executing validated tool calls."""
import time
from typing import Dict, Any, List, Optional, Callable
import logging

from ..tools.tool_registry import ToolRegistry, get_registry
from ..tools.tool_interceptor import ToolInterceptor
from ..execution.trace_ledger import TraceLedgerManager
from ..infrastructure.controller import GreenAgentController

logger = logging.getLogger(__name__)


class ToolRunner:
    """Deterministic tool runner."""
    
    def __init__(
        self,
        controller: GreenAgentController,
        tool_registry: Optional[ToolRegistry] = None,
        use_fixtures: bool = True
    ):
        """
        Initialize tool runner.
        
        Args:
            controller: Green Agent controller
            tool_registry: Optional tool registry
            use_fixtures: Whether to use fixtures
        """
        self.controller = controller
        self.tool_registry = tool_registry or get_registry()
        self.trace_ledger = TraceLedgerManager(controller)
        self.interceptor = ToolInterceptor(controller, self.tool_registry, use_fixtures)
        self._tool_functions: Dict[str, Callable] = {}
    
    def register_tool(self, tool_name: str, tool_function: Callable):
        """Register a tool function."""
        self._tool_functions[tool_name] = tool_function
    
    def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a single tool call.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            retries: Number of retries (default 0 for deterministic execution)
            
        Returns:
            Result dictionary with 'success', 'result', 'error' keys
        """
        # Validate tool call
        is_valid, error_msg = self.tool_registry.validate_tool_call(tool_name, arguments)
        if not is_valid:
            self.trace_ledger.record_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                return_value=None,
                error=error_msg
            )
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        
        # Get tool function
        tool_func = self._tool_functions.get(tool_name)
        if tool_func is None:
            error_msg = f"Tool '{tool_name}' not registered"
            self.trace_ledger.record_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                return_value=None,
                error=error_msg
            )
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        
        # Execute tool
        start_time = time.time()
        try:
            # Extract query from arguments (tools typically take query as string)
            query = arguments.get('query', '')
            result = tool_func(query)
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # Record in trace ledger
            self.trace_ledger.record_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                return_value=result,
                execution_time_ms=execution_time
            )
            
            return {
                'success': True,
                'result': result,
                'error': None,
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            self.trace_ledger.record_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                return_value=None,
                execution_time_ms=execution_time,
                error=error_msg
            )
            
            logger.error(f"Tool execution error: {error_msg}")
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time_ms': execution_time
            }
    
    def execute_plan(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a list of tool calls (plan).
        
        Args:
            tool_calls: List of tool call dicts with 'tool' and 'args' keys
            
        Returns:
            List of execution results
        """
        results = []
        for call in tool_calls:
            tool_name = call.get('tool') or call.get('tool_name')
            args = call.get('args') or call.get('arguments') or {}
            
            if not tool_name:
                results.append({
                    'success': False,
                    'result': None,
                    'error': 'Missing tool name in tool call'
                })
                continue
            
            result = self.execute_tool_call(tool_name, args)
            results.append(result)
        
        return results
    
    def get_trace_ledger(self) -> TraceLedgerManager:
        """Get trace ledger manager."""
        return self.trace_ledger

