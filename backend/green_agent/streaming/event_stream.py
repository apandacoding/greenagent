"""Event stream for real-time tool call and fixture updates."""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import json


class EventStream:
    """Manages streaming events for tool calls and fixture responses."""
    
    def __init__(self):
        """Initialize event stream."""
        self._subscribers: List[Callable] = []
        self._events: List[Dict[str, Any]] = []
    
    def subscribe(self, callback: Callable):
        """Subscribe to events."""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from events."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: Type of event ('tool_call', 'fixture_response', 'trace_update', etc.)
            data: Event data
        """
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        self._events.append(event)
        
        # Notify all subscribers
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in event subscriber: {e}")
    
    async def emit_tool_call(self, tool_name: str, arguments: Dict[str, Any], run_id: Optional[str] = None):
        """Emit tool call event."""
        await self.emit('tool_call', {
            'tool_name': tool_name,
            'arguments': arguments,
            'run_id': run_id
        })
    
    async def emit_fixture_response(
        self,
        tool_name: str,
        fixture_data: Any,
        fixture_metadata: Dict[str, Any],
        format_type: str
    ):
        """Emit fixture response event."""
        # Serialize fixture data
        if hasattr(fixture_data, 'to_dict'):
            # DataFrame
            serialized_data = fixture_data.to_dict('records')
        elif isinstance(fixture_data, dict):
            serialized_data = fixture_data
        elif isinstance(fixture_data, str):
            serialized_data = {'text': fixture_data}
        else:
            serialized_data = str(fixture_data)
        
        await self.emit('fixture_response', {
            'tool_name': tool_name,
            'data': serialized_data,
            'metadata': fixture_metadata,
            'format': format_type
        })
    
    async def emit_trace_update(self, trace: Dict[str, Any]):
        """Emit trace ledger update."""
        await self.emit('trace_update', trace)
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all events."""
        return self._events.copy()
    
    def clear_events(self):
        """Clear all events."""
        self._events.clear()


# Global event stream instance
_global_stream: Optional[EventStream] = None


def get_event_stream() -> EventStream:
    """Get global event stream instance."""
    global _global_stream
    if _global_stream is None:
        _global_stream = EventStream()
    return _global_stream

