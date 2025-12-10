"""Weather fixtures."""
from typing import Dict, Any, Optional
from .fixture_registry import FixtureRegistry


class WeatherFixtures:
    """Weather fixture loader."""
    
    def __init__(self, registry: Optional[FixtureRegistry] = None):
        self.registry = registry or FixtureRegistry()
    
    def get_fixture(
        self,
        params: Dict[str, Any],
        seed: int,
        scenario_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get weather fixture matching parameters.
        
        Args:
            params: Weather query parameters (from tool call)
            seed: Seed for deterministic selection
            scenario_id: Optional scenario ID
            
        Returns:
            Fixture data (JSON) if found, None otherwise
        """
        fixture_response = self.registry.load_fixture(
            tool_name="weather",
            params=params,
            seed=seed,
            scenario_id=scenario_id
        )
        
        if fixture_response:
            return fixture_response.data
        return None

