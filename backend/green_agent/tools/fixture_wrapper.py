"""Wrapper to intercept tool calls and return fixtures instead of API calls."""
from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime

from ..fixtures.fixture_registry import FixtureRegistry
from ..fixtures.flight_fixtures import FlightFixtures
from ..fixtures.hotel_fixtures import HotelFixtures
from ..fixtures.restaurant_fixtures import RestaurantFixtures
from ..infrastructure.controller import GreenAgentController
from ..models.fixture_models import FixtureResponse
from ..streaming.event_stream import get_event_stream
from ..streaming.event_queue import get_event_queue

logger = logging.getLogger(__name__)


class FixtureWrapper:
    """Wraps tools to intercept calls and return fixtures."""
    
    def __init__(
        self,
        controller: GreenAgentController,
        registry: Optional[FixtureRegistry] = None
    ):
        # Store last fixture data for access
        self._last_fixture_data = None
        """
        Initialize fixture wrapper.
        
        Args:
            controller: Green Agent controller for seed/scenario management
            registry: Optional fixture registry (creates new if not provided)
        """
        self.controller = controller
        self.registry = registry or FixtureRegistry()
        
        # Initialize fixture loaders
        self.flight_fixtures = FlightFixtures(self.registry)
        self.hotel_fixtures = HotelFixtures(self.registry)
        self.restaurant_fixtures = RestaurantFixtures(self.registry)
        
        # Track intercepted calls for logging
        self.intercepted_calls: list[Dict[str, Any]] = []
        
        # Event stream for real-time updates
        self.event_stream = get_event_stream()
        self.event_queue = get_event_queue()
    
    def wrap_tool(self, tool_name: str, original_tool: Callable) -> Callable:
        """
        Wrap a tool to intercept calls and return fixtures.
        
        Args:
            tool_name: Name of the tool
            original_tool: Original tool function
            
        Returns:
            Wrapped tool function
        """
        def wrapped_tool(*args, **kwargs):
            # Extract query/params from tool call
            # Tools typically take 'query' as first arg or in kwargs
            if args and len(args) > 0:
                query = args[0]
            else:
                query = kwargs.get('query', '')
            
            # Build params dict for fixture lookup
            params = {'query': str(query)}
            params.update(kwargs)
            
            # Get seed and scenario from controller
            seed = self.controller.get_seed()
            scenario_id = self.controller.get_scenario_id()
            
            # Try to load fixture
            fixture_data = None
            fixture_metadata = None
            
            if tool_name == "flight_search":
                fixture_data = self.flight_fixtures.get_fixture(params, seed, scenario_id)
            elif tool_name == "hotel_search":
                fixture_data = self.hotel_fixtures.get_fixture(params, seed, scenario_id)
            elif tool_name == "restaurant_search":
                fixture_data = self.restaurant_fixtures.get_fixture(params, seed, scenario_id)
            
            # Emit tool call event immediately (sync-safe via queue)
            run_id = self.controller.get_run_id()
            logger.info(f"[FixtureWrapper] Tool called: {tool_name} with params: {params}, run_id: {run_id}")
            try:
                event = {
                    'type': 'tool_call',
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'tool_name': tool_name,
                        'arguments': params,
                        'run_id': run_id
                    }
                }
                logger.info(f"[FixtureWrapper] Emitting tool_call event for {tool_name}, event: {event}")
                self.event_queue.put(event)
                logger.info(f"[FixtureWrapper] Event queued successfully for {tool_name}")
            except Exception as e:
                logger.error(f"[FixtureWrapper] Failed to queue tool call event: {e}", exc_info=True)
            
            # If fixture found, return it
            if fixture_data is not None:
                # Load full fixture response to get metadata
                fixture_response = self.registry.load_fixture(
                    tool_name=tool_name,
                    params=params,
                    seed=seed,
                    scenario_id=scenario_id
                )
                
                if fixture_response:
                    fixture_metadata = fixture_response.metadata
                    
                    # Emit fixture response event immediately (sync-safe via queue)
                    logger.info(f"[FixtureWrapper] Found fixture for {tool_name}, emitting fixture_response event")
                    try:
                        # Serialize fixture data for JSON
                        serialized_data = fixture_data
                        if hasattr(fixture_data, 'to_dict'):
                            # DataFrame
                            serialized_data = fixture_data.to_dict('records')
                            logger.info(f"[FixtureWrapper] Serialized DataFrame to {len(serialized_data)} records")
                        elif isinstance(fixture_data, dict):
                            serialized_data = fixture_data
                            logger.info(f"[FixtureWrapper] Using dict data with {len(serialized_data)} keys")
                        elif isinstance(fixture_data, str):
                            serialized_data = {'text': fixture_data}
                        else:
                            serialized_data = str(fixture_data)
                        
                        event = {
                            'type': 'fixture_response',
                            'timestamp': datetime.now().isoformat(),
                            'data': {
                                'tool_name': tool_name,
                                'data': serialized_data,
                                'metadata': fixture_metadata.model_dump(),
                                'format': fixture_response.format
                            }
                        }
                        logger.info(f"[FixtureWrapper] Emitting fixture_response event for {tool_name}")
                        self.event_queue.put(event)
                        logger.info(f"[FixtureWrapper] Fixture response event queued successfully")
                    except Exception as e:
                        logger.error(f"[FixtureWrapper] Failed to queue fixture response event: {e}", exc_info=True)
                
                # Store raw fixture data for later access (before any conversions)
                self._last_fixture_data = fixture_data
                
                # Log intercepted call
                intercepted = {
                    'tool_name': tool_name,
                    'params': params,
                    'seed': seed,
                    'scenario_id': scenario_id,
                    'metadata': fixture_metadata.model_dump() if fixture_metadata else None,
                    'response_format': fixture_response.format if fixture_response else None,
                    'raw_data': fixture_data  # Store raw data in intercepted calls too
                }
                self.intercepted_calls.append(intercepted)
                
                logger.info(f"Intercepted {tool_name} call, returning fixture (seed={seed}). Raw data type: {type(fixture_data).__name__}")
                
                # Return fixture data in format expected by tool
                # Tools need to return strings for AgentExecutor, but we've stored raw data in _last_fixture_data
                if fixture_response and fixture_response.format == 'dataframe':
                    # For DataFrames, we need to return a string but store the DataFrame
                    # The raw DataFrame is stored in _last_fixture_data and intercepted_calls
                    if hasattr(fixture_data, 'to_json'):
                        # Convert DataFrame to JSON string for AgentExecutor
                        return fixture_data.to_json(orient='records', date_format='iso')
                    elif hasattr(fixture_data, 'to_string'):
                        return fixture_data.to_string()
                    else:
                        return str(fixture_data)
                elif fixture_response and fixture_response.format == 'json':
                    # Return JSON string for AgentExecutor
                    if isinstance(fixture_data, str):
                        return fixture_data
                    elif isinstance(fixture_data, dict):
                        import json
                        return json.dumps(fixture_data, indent=2)
                    return fixture_data
                else:
                    # Fallback: return as string but raw data is stored in _last_fixture_data
                    return str(fixture_data) if not isinstance(fixture_data, str) else fixture_data
            
            # No fixture found - fall back to original tool (or return error)
            logger.warning(f"No fixture found for {tool_name}, falling back to original tool")
            result = original_tool(*args, **kwargs)
            # Store the result as last fixture data even if it's from original tool
            self._last_fixture_data = result
            return result
        
        return wrapped_tool
    
    def get_intercepted_calls(self) -> list[Dict[str, Any]]:
        """Get list of all intercepted tool calls."""
        return self.intercepted_calls.copy()
    
    def clear_intercepted_calls(self):
        """Clear intercepted calls log."""
        self.intercepted_calls = []

