"""Controller for managing Green Agent execution state."""
from typing import Optional, Dict, Any
from .seed_manager import SeedManager


class GreenAgentController:
    """Controller managing Green Agent execution state and seed."""
    
    def __init__(self, seed: Optional[int] = None, scenario_id: Optional[str] = None):
        """
        Initialize controller.
        
        Args:
            seed: Seed for deterministic execution
            scenario_id: Optional scenario identifier
        """
        self.seed_manager = SeedManager(seed)
        self.scenario_id = scenario_id
        self.run_id: Optional[str] = None
        self._state: Dict[str, Any] = {}
    
    def start_run(self, run_id: Optional[str] = None) -> str:
        """
        Start a new run.
        
        Args:
            run_id: Optional run ID. Generated if not provided.
            
        Returns:
            The run ID for this execution
        """
        if run_id is None:
            import uuid
            run_id = str(uuid.uuid4())
        
        self.run_id = run_id
        self._state = {}
        return run_id
    
    def get_seed(self) -> int:
        """Get current seed."""
        return self.seed_manager.get_seed()
    
    def get_scenario_id(self) -> Optional[str]:
        """Get scenario ID."""
        return self.scenario_id
    
    def get_run_id(self) -> Optional[str]:
        """Get current run ID."""
        return self.run_id
    
    def get_run_hash(self) -> Optional[str]:
        """Get hash of current run ID."""
        if self.run_id:
            return self.seed_manager.hash_run_id(self.run_id)
        return None
    
    def reset(self, seed: Optional[int] = None):
        """Reset controller state."""
        if seed is not None:
            self.seed_manager.set_seed(seed)
        else:
            self.seed_manager.reset()
        self.run_id = None
        self._state = {}
    
    def set_state(self, key: str, value: Any):
        """Set state value."""
        self._state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self._state.get(key, default)

