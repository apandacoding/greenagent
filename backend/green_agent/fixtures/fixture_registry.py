"""Fixture registry for managing and loading fixtures."""
import json
import os
import hashlib
from typing import Dict, Any, Optional, Union
from pathlib import Path
import pandas as pd

from ..models.fixture_models import FixtureResponse, FixtureMetadata


class FixtureRegistry:
    """Registry for managing fixtures by tool name, seed, and parameters."""
    
    def __init__(self, fixtures_dir: Optional[str] = None):
        """
        Initialize fixture registry.
        
        Args:
            fixtures_dir: Base directory for fixture files. Defaults to fixtures/ in package.
        """
        if fixtures_dir is None:
            base_dir = Path(__file__).parent
            self.fixtures_dir = base_dir / "data"
        else:
            self.fixtures_dir = Path(fixtures_dir)
        
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = {}
    
    def _hash_params(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate hash for tool params to match fixtures."""
        # Normalize params for consistent hashing
        normalized = {
            "tool": tool_name,
            **{k: str(v).lower().strip() for k, v in sorted(params.items())}
        }
        param_str = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def _get_fixture_path(self, tool_name: str, seed: int, param_hash: Optional[str] = None) -> Path:
        """Get path to fixture file."""
        if param_hash:
            return self.fixtures_dir / tool_name / f"{seed}_{param_hash}.json"
        return self.fixtures_dir / tool_name / f"{seed}.json"
    
    def load_fixture(
        self,
        tool_name: str,
        params: Dict[str, Any],
        seed: int,
        scenario_id: Optional[str] = None
    ) -> Optional[FixtureResponse]:
        """
        Load fixture matching tool call parameters and seed.
        
        Args:
            tool_name: Name of the tool (e.g., 'flight_search')
            params: Tool call parameters
            seed: Seed for deterministic selection
            scenario_id: Optional scenario ID
            
        Returns:
            FixtureResponse if found, None otherwise
        """
        param_hash = self._hash_params(tool_name, params)
        
        # Try to find fixture with exact param match first
        fixture_path = self._get_fixture_path(tool_name, seed, param_hash)
        
        if not fixture_path.exists():
            # Fall back to seed-only fixture
            fixture_path = self._get_fixture_path(tool_name, seed)
        
        if not fixture_path.exists():
            return None
        
        # Check cache
        cache_key = f"{tool_name}:{seed}:{param_hash}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load fixture
        try:
            with open(fixture_path, 'r') as f:
                fixture_data = json.load(f)
            
            # Determine format
            data = fixture_data.get('data')
            format_type = fixture_data.get('format', 'json')
            
            # Convert to DataFrame if needed
            if format_type == 'dataframe' and isinstance(data, dict):
                data = pd.DataFrame(data.get('records', []))
            elif format_type == 'dataframe' and isinstance(data, list):
                data = pd.DataFrame(data)
            
            metadata = FixtureMetadata(
                seed=seed,
                scenario_id=scenario_id or fixture_data.get('scenario_id'),
                source_file=str(fixture_path),
                perturbation_applied=fixture_data.get('perturbation'),
                tool_name=tool_name,
                created_at=fixture_data.get('created_at')
            )
            
            response = FixtureResponse(
                data=data,
                metadata=metadata,
                format=format_type
            )
            
            # Cache response
            self._cache[cache_key] = response
            return response
            
        except Exception as e:
            print(f"Error loading fixture from {fixture_path}: {e}")
            return None
    
    def save_fixture(
        self,
        tool_name: str,
        params: Dict[str, Any],
        seed: int,
        data: Union[Dict[str, Any], pd.DataFrame, str],
        format_type: str = 'json',
        scenario_id: Optional[str] = None,
        perturbation: Optional[str] = None
    ):
        """
        Save a fixture to disk.
        
        Args:
            tool_name: Name of the tool
            params: Tool call parameters
            seed: Seed value
            data: Response data (JSON dict, DataFrame, or string)
            format_type: Format type ('json', 'dataframe', 'text')
            scenario_id: Optional scenario ID
            perturbation: Optional perturbation description
        """
        param_hash = self._hash_params(tool_name, params)
        fixture_path = self._get_fixture_path(tool_name, seed, param_hash)
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for JSON serialization
        if isinstance(data, pd.DataFrame):
            serialized_data = {'records': data.to_dict('records')}
        elif isinstance(data, dict):
            serialized_data = data
        else:
            serialized_data = {'text': str(data)}
        
        fixture_dict = {
            'tool_name': tool_name,
            'seed': seed,
            'scenario_id': scenario_id,
            'format': format_type,
            'perturbation': perturbation,
            'params': params,
            'data': serialized_data,
            'created_at': pd.Timestamp.now().isoformat()
        }
        
        with open(fixture_path, 'w') as f:
            json.dump(fixture_dict, f, indent=2, default=str)

