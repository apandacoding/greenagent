"""Isolation system for preventing cross-run contamination."""
from typing import Dict, Any, Optional
import threading


class Isolator:
    """Provides isolation between runs to prevent contamination."""
    
    def __init__(self):
        """Initialize isolator."""
        self._local_state = threading.local()
        self._global_state: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def reset(self):
        """Reset all state for clean run."""
        with self._lock:
            self._global_state.clear()
        
        # Clear thread-local state
        if hasattr(self._local_state, 'state'):
            self._local_state.state = {}
    
    def set_global(self, key: str, value: Any):
        """Set global state (protected by lock)."""
        with self._lock:
            self._global_state[key] = value
    
    def get_global(self, key: str, default: Any = None) -> Any:
        """Get global state."""
        with self._lock:
            return self._global_state.get(key, default)
    
    def clear_global(self, key: str):
        """Clear global state key."""
        with self._lock:
            self._global_state.pop(key, None)
    
    def set_local(self, key: str, value: Any):
        """Set thread-local state."""
        if not hasattr(self._local_state, 'state'):
            self._local_state.state = {}
        self._local_state.state[key] = value
    
    def get_local(self, key: str, default: Any = None) -> Any:
        """Get thread-local state."""
        if not hasattr(self._local_state, 'state'):
            return default
        return self._local_state.state.get(key, default)
    
    def clear_local(self, key: str):
        """Clear thread-local state key."""
        if hasattr(self._local_state, 'state'):
            self._local_state.state.pop(key, None)


# Global isolator instance
_isolator: Optional[Isolator] = None


def get_isolator() -> Isolator:
    """Get global isolator instance."""
    global _isolator
    if _isolator is None:
        _isolator = Isolator()
    return _isolator

