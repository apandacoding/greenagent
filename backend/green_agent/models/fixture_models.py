"""Models for fixture data structures."""
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
import pandas as pd


class FixtureMetadata(BaseModel):
    """Metadata about a fixture."""
    seed: int
    scenario_id: Optional[str] = None
    source_file: Optional[str] = None
    perturbation_applied: Optional[str] = None
    tool_name: str
    created_at: Optional[str] = None


class FixtureResponse(BaseModel):
    """Fixture response container."""
    data: Union[Dict[str, Any], pd.DataFrame, str]
    metadata: FixtureMetadata
    format: str  # 'json', 'dataframe', 'text'
    
    class Config:
        arbitrary_types_allowed = True

