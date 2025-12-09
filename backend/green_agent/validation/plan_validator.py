"""Plan validator for tool execution plans."""
import json
from typing import List, Dict, Any, Optional, Tuple

from ..tools.tool_registry import ToolRegistry, get_registry
from .normalizer import PlanNormalizer


class PlanValidator:
    """Validates tool execution plans."""
    
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """
        Initialize plan validator.
        
        Args:
            tool_registry: Optional tool registry
        """
        self.tool_registry = tool_registry or get_registry()
        self.normalizer = PlanNormalizer()
    
    def validate_plan(self, plan: Any, allow_normalization: bool = True) -> Tuple[bool, Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Validate a tool plan.
        
        Args:
            plan: Plan to validate (should be JSON-serializable list of tool calls)
            allow_normalization: Whether to apply safe normalizations
            
        Returns:
            Tuple of (is_valid, error_message, normalized_plan)
        """
        # Must be JSON (not natural language)
        if isinstance(plan, str):
            # Try to parse as JSON
            try:
                plan = json.loads(plan)
            except json.JSONDecodeError:
                return False, "Plan must be valid JSON, not natural language", None
        
        # Must be a list
        if not isinstance(plan, list):
            return False, "Plan must be a list of tool calls", None
        
        if len(plan) == 0:
            return False, "Plan cannot be empty", None
        
        # Validate each tool call
        normalized_calls = []
        for i, call in enumerate(plan):
            # Must be a dict
            if not isinstance(call, dict):
                return False, f"Tool call {i} must be a dictionary", None
            
            # Must have 'tool' or 'tool_name' field
            tool_name = call.get('tool') or call.get('tool_name')
            if not tool_name:
                return False, f"Tool call {i} missing 'tool' or 'tool_name' field", None
            
            # Check tool is in allow-list
            if not self.tool_registry.is_allowed(tool_name):
                allowed = ', '.join(self.tool_registry.get_allowed_tools())
                return False, f"Tool '{tool_name}' is not allowed. Allowed tools: {allowed}", None
            
            # Get arguments
            args = call.get('args') or call.get('arguments') or {}
            if not isinstance(args, dict):
                return False, f"Tool call {i} 'args' must be a dictionary", None
            
            # Validate tool call arguments
            is_valid, error = self.tool_registry.validate_tool_call(tool_name, args)
            if not is_valid:
                return False, f"Tool call {i} ({tool_name}): {error}", None
            
            # Normalize if allowed
            if allow_normalization:
                normalized_call = {
                    'tool': tool_name,
                    'args': self.normalizer.normalize_value(args)
                }
                normalized_calls.append(normalized_call)
            else:
                normalized_calls.append({
                    'tool': tool_name,
                    'args': args
                })
        
        return True, None, normalized_calls
    
    def validate_and_normalize(self, plan: Any) -> Tuple[bool, Optional[str], Optional[List[Dict[str, Any]]]]:
        """Validate and normalize a plan."""
        return self.validate_plan(plan, allow_normalization=True)

