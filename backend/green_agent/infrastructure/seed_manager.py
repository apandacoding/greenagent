"""Seed management for deterministic execution."""
import random
import hashlib
from typing import Optional


class SeedManager:
    """Manages deterministic seed for fixtures and perturbations."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize seed manager.
        
        Args:
            seed: Initial seed. If None, generates from system state.
        """
        if seed is None:
            # Generate deterministic seed from current state
            seed = self._generate_seed()
        
        self._initial_seed = seed
        self._current_seed = seed
        self._random_state = random.Random(seed)
    
    @staticmethod
    def _generate_seed() -> int:
        """Generate a seed from system state."""
        import time
        return int(time.time() * 1000) % (2**31)
    
    def reset(self, seed: Optional[int] = None):
        """Reset to initial seed or provided seed."""
        if seed is None:
            seed = self._initial_seed
        self._current_seed = seed
        self._random_state = random.Random(seed)
    
    def get_seed(self) -> int:
        """Get current seed."""
        return self._current_seed
    
    def set_seed(self, seed: int):
        """Set new seed."""
        self._current_seed = seed
        self._random_state = random.Random(seed)
    
    def get_random(self) -> random.Random:
        """Get deterministic random instance."""
        return self._random_state
    
    def derive_seed(self, context: str) -> int:
        """
        Derive a deterministic seed from current seed and context.
        
        Useful for creating sub-seeds for specific tools or perturbations.
        """
        combined = f"{self._current_seed}:{context}"
        return int(hashlib.md5(combined.encode()).hexdigest()[:8], 16) % (2**31)
    
    def hash_run_id(self, run_id: str) -> str:
        """Generate hash of run ID for trace ledger."""
        combined = f"{self._current_seed}:{run_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

