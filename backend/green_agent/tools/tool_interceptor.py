"""Tool interceptor for wrapping LangChain tools to use fixtures."""
from typing import Dict, Any, Optional
import logging

from langchain.tools import BaseTool
from .fixture_wrapper import FixtureWrapper
from .tool_registry import ToolRegistry, get_registry
from ..infrastructure.controller import GreenAgentController

logger = logging.getLogger(__name__)


class ToolInterceptor:
    """Intercepts tool calls and routes to fixtures."""
    
    def __init__(
        self,
        controller: GreenAgentController,
        registry: Optional[ToolRegistry] = None,
        use_fixtures: bool = True
    ):
        """
        Initialize tool interceptor.
        
        Args:
            controller: Green Agent controller
            registry: Optional tool registry
            use_fixtures: Whether to use fixtures (True) or real APIs (False)
        """
        self.controller = controller
        self.tool_registry = registry or get_registry()
        self.use_fixtures = use_fixtures
        self.fixture_wrapper = FixtureWrapper(controller) if use_fixtures else None
    
    def intercept_tool(self, tool: BaseTool) -> BaseTool:
        """
        Intercept a LangChain tool to use fixtures.
        
        Args:
            tool: Original LangChain tool
            
        Returns:
            Wrapped tool that uses fixtures
        """
        if not self.use_fixtures:
            return tool
        
        # Validate tool is allowed
        tool_name = tool.name
        if not self.tool_registry.is_allowed(tool_name):
            logger.warning(f"Tool {tool_name} not in allow-list, but allowing (may need registration)")
        
        # Create wrapper class with captured variables
        original_run = tool._run
        original_arun = tool._arun
        tool_registry_ref = self.tool_registry
        fixture_wrapper_ref = self.fixture_wrapper
        
        class InterceptedTool(BaseTool):
            name: str = tool.name
            description: str = tool.description
            
            def _run(self, query: str) -> str:
                # Validate tool call
                args = {'query': query}
                is_valid, error = tool_registry_ref.validate_tool_call(tool_name, args)
                if not is_valid:
                    logger.error(f"Invalid tool call: {error}")
                    return f"Error: {error}"
                
                # Get fixture
                if fixture_wrapper_ref:
                    return fixture_wrapper_ref.wrap_tool(tool_name, original_run)(query)
                
                return original_run(query)
            
            async def _arun(self, query: str):
                # For async, we'll handle it synchronously for now
                # In production, you'd want proper async fixture loading
                return self._run(query)
        
        intercepted = InterceptedTool()
        
        # Copy over any additional attributes
        for attr in dir(tool):
            if not attr.startswith('_') and not hasattr(intercepted, attr):
                try:
                    setattr(intercepted, attr, getattr(tool, attr))
                except:
                    pass
        
        return intercepted
    
    def get_intercepted_calls(self) -> list[Dict[str, Any]]:
        """Get intercepted tool calls."""
        if self.fixture_wrapper:
            return self.fixture_wrapper.get_intercepted_calls()
        return []

