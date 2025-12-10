"""Tool registry for whitelisting and validating tools."""
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass


@dataclass
class ToolSpec:
    """Specification for a tool."""
    name: str
    required_args: Set[str]
    optional_args: Set[str] = None
    arg_types: Dict[str, type] = None
    
    def __post_init__(self):
        if self.optional_args is None:
            self.optional_args = set()
        if self.arg_types is None:
            self.arg_types = {}


class ToolRegistry:
    """Registry of allowed tools with validation rules."""
    
    def __init__(self):
        """Initialize tool registry with default tools."""
        self._tools: Dict[str, ToolSpec] = {}
        self._initialize_default_tools()
    
    def _initialize_default_tools(self):
        """Register default tools."""
        # Flight search tool
        self.register_tool(ToolSpec(
            name="flight_search",
            required_args={"query"},
            arg_types={"query": str}
        ))
        
        # Hotel search tool
        self.register_tool(ToolSpec(
            name="hotel_search",
            required_args={"query"},
            arg_types={"query": str}
        ))
        
        # Restaurant search tool
        self.register_tool(ToolSpec(
            name="restaurant_search",
            required_args={"query"},
            arg_types={"query": str}
        ))
        
        # Weather tool (optional)
        self.register_tool(ToolSpec(
            name="weather",
            required_args={"query"},
            arg_types={"query": str}
        ))
    
    def register_tool(self, spec: ToolSpec):
        """Register a tool specification."""
        self._tools[spec.name] = spec
    
    def is_allowed(self, tool_name: str) -> bool:
        """Check if tool is in allow-list."""
        return tool_name in self._tools
    
    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate tool call arguments.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_allowed(tool_name):
            return False, f"Tool '{tool_name}' is not in the allow-list"
        
        spec = self._tools[tool_name]
        
        # Check required args
        for req_arg in spec.required_args:
            if req_arg not in args:
                return False, f"Missing required argument: {req_arg}"
            
            # Check if non-empty
            value = args[req_arg]
            if value is None or (isinstance(value, str) and not value.strip()):
                return False, f"Required argument '{req_arg}' is empty"
        
        # Check arg types if specified
        for arg_name, arg_type in spec.arg_types.items():
            if arg_name in args:
                value = args[arg_name]
                if value is not None and not isinstance(value, arg_type):
                    return False, f"Argument '{arg_name}' must be of type {arg_type.__name__}, got {type(value).__name__}"
        
        return True, None
    
    def get_allowed_tools(self) -> List[str]:
        """Get list of all allowed tool names."""
        return list(self._tools.keys())
    
    def get_tool_spec(self, tool_name: str) -> Optional[ToolSpec]:
        """Get tool specification."""
        return self._tools.get(tool_name)


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

