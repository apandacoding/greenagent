"""ReAct callback handler to capture AgentExecutor operations."""
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.agents import AgentAction, AgentFinish

from .event_queue import get_event_queue

logger = logging.getLogger(__name__)


class ReActCallbackHandler(AsyncCallbackHandler):
    """Callback handler that captures ReAct loop operations and emits events."""
    
    def __init__(self, event_queue=None):
        """Initialize callback handler.
        
        Args:
            event_queue: Event queue instance (uses global if None)
        """
        super().__init__()
        self.event_queue = event_queue or get_event_queue()
        self.current_step = None
        self.tool_outputs = {}
    
    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts generating a response (Thought step)."""
        logger.debug("[ReActCallback] LLM started - Thought step")
        
        # Extract the prompt to identify if this is a Thought or Final Answer
        if prompts:
            prompt_text = prompts[0]
            if "Thought:" in prompt_text or "thought" in prompt_text.lower():
                self.current_step = {
                    'type': 'thought',
                    'timestamp': datetime.now().isoformat()
                }
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes generating a response."""
        logger.debug("[ReActCallback] LLM ended")
        
        if response and response.generations:
            generation = response.generations[0][0] if response.generations[0] else None
            if generation:
                text = generation.text
                
                # Determine if this is Thought, Action, or Final Answer
                if "Thought:" in text:
                    thought_text = text.split("Thought:")[-1].split("Action:")[0].strip()
                    self._emit_event({
                        'type': 'react_step',
                        'step_type': 'thought',
                        'content': thought_text,
                        'timestamp': datetime.now().isoformat()
                    })
                elif "Final Answer:" in text:
                    answer_text = text.split("Final Answer:")[-1].strip()
                    self._emit_event({
                        'type': 'react_step',
                        'step_type': 'final_answer',
                        'content': answer_text,
                        'timestamp': datetime.now().isoformat()
                    })
    
    async def on_agent_action(
        self, action: AgentAction, **kwargs: Any
    ) -> None:
        """Called when agent decides to take an action (calls a tool)."""
        logger.info(f"[ReActCallback] Agent action: {action.tool} with input: {action.tool_input}")
        
        self._emit_event({
            'type': 'react_step',
            'step_type': 'action',
            'tool': action.tool,
            'tool_input': action.tool_input,
            'log': action.log,
            'timestamp': datetime.now().isoformat()
        })
    
    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when a tool starts executing."""
        tool_name = serialized.get("name", "unknown")
        logger.info(f"[ReActCallback] Tool started: {tool_name}")
        
        self._emit_event({
            'type': 'react_step',
            'step_type': 'tool_start',
            'tool': tool_name,
            'input': input_str,
            'timestamp': datetime.now().isoformat()
        })
    
    async def on_tool_end(
        self, output: str, **kwargs: Any
    ) -> None:
        """Called when a tool finishes executing."""
        logger.info(f"[ReActCallback] Tool ended with output length: {len(output) if output else 0}")
        
        # Try to extract tool name from kwargs
        tool_name = kwargs.get("name", "unknown")
        
        self._emit_event({
            'type': 'react_step',
            'step_type': 'observation',
            'tool': tool_name,
            'output': output[:1000] if output and len(output) > 1000 else output,  # Truncate long outputs
            'output_length': len(output) if output else 0,
            'timestamp': datetime.now().isoformat()
        })
    
    async def on_tool_error(
        self, error: Exception, **kwargs: Any
    ) -> None:
        """Called when a tool encounters an error."""
        logger.error(f"[ReActCallback] Tool error: {error}")
        
        tool_name = kwargs.get("name", "unknown")
        
        self._emit_event({
            'type': 'react_step',
            'step_type': 'tool_error',
            'tool': tool_name,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
    
    async def on_agent_finish(
        self, finish: AgentFinish, **kwargs: Any
    ) -> None:
        """Called when agent finishes (returns final answer)."""
        logger.info("[ReActCallback] Agent finished")
        
        self._emit_event({
            'type': 'react_step',
            'step_type': 'agent_finish',
            'output': finish.return_values.get("output", ""),
            'timestamp': datetime.now().isoformat()
        })
    
    def _emit_event(self, event_data: Dict[str, Any]) -> None:
        """Emit event via event queue (synchronous, thread-safe)."""
        try:
            self.event_queue.put(event_data)
            logger.debug(f"[ReActCallback] Event emitted: {event_data.get('step_type', 'unknown')}")
        except Exception as e:
            logger.error(f"[ReActCallback] Failed to emit event: {e}", exc_info=True)

