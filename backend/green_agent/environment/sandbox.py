"""Sandbox environment with deterministic execution constraints."""
import os
import sys
import random
from typing import Optional
from contextlib import contextmanager

from ..infrastructure.seed_manager import SeedManager


class Sandbox:
    """Sandbox environment with no network and deterministic execution."""
    
    def __init__(self, seed: Optional[int] = None, disable_network: bool = True):
        """
        Initialize sandbox.
        
        Args:
            seed: Seed for deterministic randomness
            disable_network: Whether to disable network access
        """
        self.seed_manager = SeedManager(seed)
        self.disable_network = disable_network
        self._original_random_state = None
        self._network_blocked = False
    
    def __enter__(self):
        """Enter sandbox context."""
        # Set deterministic random seed
        self._original_random_state = random.getstate()
        seed = self.seed_manager.get_seed()
        random.seed(seed)
        
        # Disable network if requested
        if self.disable_network:
            self._block_network()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context."""
        # Restore random state
        if self._original_random_state:
            random.setstate(self._original_random_state)
        
        # Restore network
        if self._network_blocked:
            self._unblock_network()
    
    def _block_network(self):
        """Block network access by monkey-patching socket/requests."""
        # This is a simple implementation - in production you'd want more robust blocking
        self._network_blocked = True
        
        # Store original imports
        if not hasattr(self, '_original_socket'):
            import socket
            self._original_socket = socket.socket
            
            def blocked_socket(*args, **kwargs):
                raise RuntimeError("Network access blocked in sandbox mode")
            
            socket.socket = blocked_socket
    
    def _unblock_network(self):
        """Restore network access."""
        if self._network_blocked and hasattr(self, '_original_socket'):
            import socket
            socket.socket = self._original_socket
            self._network_blocked = False
    
    @contextmanager
    def tool_call_logging(self):
        """
        Context manager for logging tool calls.
        
        Usage:
            with sandbox.tool_call_logging() as logger:
                # tool calls are logged here
        """
        class ToolCallLogger:
            def __init__(self):
                self.calls = []
            
            def log(self, tool_name: str, args: dict, result: any):
                self.calls.append({
                    'tool': tool_name,
                    'args': args,
                    'result': result
                })
        
        logger = ToolCallLogger()
        yield logger
    
    def get_seed(self) -> int:
        """Get current seed."""
        return self.seed_manager.get_seed()

