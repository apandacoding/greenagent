"""Integration with existing chatbot codebase."""
from typing import Dict, Any, Optional, List, Tuple
import logging
import time
import hashlib

from .green_agent import GreenAgent as NewGreenAgent
from .tools.tool_interceptor import ToolInterceptor
from .infrastructure.controller import GreenAgentController
from .execution.trace_ledger import TraceLedgerManager

logger = logging.getLogger(__name__)

# Global tool call tracking per execution (reset for each new execution)
_tool_call_counts: Dict[str, int] = {}
_tool_failures: Dict[str, str] = {}  # Track permanent failures: tool_name -> error_message
_tool_successes: Dict[str, str] = {}  # Track successful tool calls by key -> return_value summary


def reset_tool_call_tracking():
    """Reset tool call tracking for a new execution."""
    global _tool_call_counts, _tool_failures, _tool_successes
    _tool_call_counts.clear()
    _tool_failures.clear()
    _tool_successes.clear()
    logger.info("[Integration] Tool call tracking reset for new execution")


def normalize_query(query: str) -> str:
    """Normalize query to detect similar/duplicate calls."""
    import re
    
    # Remove extra whitespace, convert to lowercase, remove trailing newlines
    normalized = " ".join(query.lower().strip().split())
    original_upper = query.upper()  # Keep original for airport code extraction
    
    # Map city names to canonical airport codes
    city_to_code = {
        'los angeles': 'LAX', 'lax': 'LAX',
        'new york': 'NYC', 'nyc': 'NYC', 'jfk': 'NYC', 'ewr': 'NYC', 'lga': 'NYC',
        'san francisco': 'SFO', 'sfo': 'SFO',
        'chicago': 'ORD', 'ord': 'ORD',
        'miami': 'MIA', 'mia': 'MIA',
        'barcelona': 'BCN', 'bcn': 'BCN',
        'tokyo': 'NRT', 'nrt': 'NRT', 'hnd': 'NRT',
    }
    
    # Extract airport codes (3 uppercase letters)
    airport_codes = re.findall(r'\b[A-Z]{3}\b', original_upper)
    
    # Extract dates (multiple formats)
    date_patterns = [
        (r'\d{4}-\d{2}-\d{2}', lambda m: m.group(0)),  # 2026-03-15
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),  # 3/15/2026 -> 2026-03-15
        (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', lambda m: m.group(3) + "-XX-XX"),  # March 15, 2026 -> 2026-XX-XX (partial match)
    ]
    dates = []
    for pattern, formatter in date_patterns:
        for match in re.finditer(pattern, normalized):
            dates.append(formatter(match))
    
    # For flight queries, build a signature from route and dates
    if 'flight' in normalized or 'fly' in normalized or any(code in airport_codes for code in ['LAX', 'NYC', 'SFO', 'JFK', 'EWR', 'LGA', 'BCN']):
        parts = []
        
        # Normalize airport codes from city names in query
        normalized_lower = normalized.lower()
        found_codes = []
        
        # Check for city names first (before airport codes)
        for city, code in city_to_code.items():
            if city in normalized_lower:
                found_codes.append(code)
                # Remove the city name to avoid double matching
                normalized_lower = normalized_lower.replace(city, '')
        
        # Add explicit airport codes
        for code in airport_codes:
            if code not in found_codes:
                found_codes.append(code)
        
        # Build route signature (first 2 codes = origin-destination)
        if len(found_codes) >= 2:
            # Try to determine order from query text
            first_idx = min([normalized_lower.find(code.lower()) for code in found_codes[:2] if code.lower() in normalized_lower], default=0)
            second_idx = max([normalized_lower.find(code.lower()) for code in found_codes[:2] if code.lower() in normalized_lower], default=0)
            
            if first_idx < second_idx:
                parts.append(f"{found_codes[0]}-{found_codes[1]}")
            else:
                parts.append(f"{found_codes[1]}-{found_codes[0]}")
        elif len(found_codes) == 1:
            parts.append(found_codes[0])
        
        # Add dates (normalized to YYYY-MM-DD format, sorted)
        if dates:
            # Sort and dedupe dates
            unique_dates = sorted(set(dates))
            parts.extend(unique_dates)
        
        if parts:
            # Signature: "LAX-NYC:2026-03-15:2026-03-22"
            return ":".join(parts)
    
    # Fallback: return normalized query for hashing
    return normalized


def get_tool_call_key(tool_name: str, query: str) -> str:
    """Generate a unique key for a tool call to track duplicates."""
    normalized = normalize_query(query)
    # Use hash for efficiency, but include tool name for uniqueness
    key = f"{tool_name}:{hashlib.md5(normalized.encode()).hexdigest()}"
    return key


def check_and_increment_tool_call(tool_name: str, query: str) -> Tuple[bool, int, Optional[str]]:
    """
    Check if tool call exceeds limit and increment counter.
    
    Returns:
        (should_block, current_count, failure_reason): 
        - should_block: True if should block (>= 2 attempts or permanent failure)
        - current_count: count of attempts
        - failure_reason: reason for blocking (if any)
    """
    global _tool_call_counts, _tool_failures, _tool_successes
    
    # Check if this tool has already permanently failed (returned PERMANENT_FAILURE)
    if tool_name in _tool_failures:
        failure_msg = _tool_failures[tool_name]
        logger.warning(f"[Integration] ⚠️ Tool {tool_name} has permanent failure, blocking retry: {failure_msg[:100]}")
        return True, 999, f"Permanent failure: {failure_msg[:100]}"
    
    key = get_tool_call_key(tool_name, query)
    
    # Block if we already succeeded with this tool/query combo
    if key in _tool_successes:
        logger.info(f"[Integration] ✅ Tool {tool_name} already succeeded for this query; reusing prior result.")
        return True, 1, "Already succeeded"
    
    count = _tool_call_counts.get(key, 0)
    
    if count >= 2:
        logger.warning(f"[Integration] ⚠️ Tool {tool_name} already called {count} times with similar query, blocking duplicate")
        return True, count, f"Maximum retry limit (2) reached for this query"
    
    # Increment counter
    _tool_call_counts[key] = count + 1
    logger.info(f"[Integration] Tool {tool_name} attempt #{_tool_call_counts[key]} for query: {normalize_query(query)[:100]}...")
    return False, _tool_call_counts[key], None


def record_tool_failure(tool_name: str, error_message: str):
    """Record a permanent failure for a tool to prevent future retries."""
    global _tool_failures
    if "PERMANENT_FAILURE" in error_message or "permanent failure" in error_message.lower():
        _tool_failures[tool_name] = error_message
        logger.warning(f"[Integration] ⚠️ Recorded permanent failure for {tool_name}: {error_message[:100]}")


def record_tool_success(tool_name: str, query: str, return_value: str):
    """Record a successful tool call to prevent further duplicates in this execution."""
    global _tool_successes
    key = get_tool_call_key(tool_name, query)
    _tool_successes[key] = return_value[:200]  # store a short summary


def wrap_white_agent_tools(
    white_agent_instance,
    controller: GreenAgentController,
    use_fixtures: bool = True,
    trace_ledger: Optional[TraceLedgerManager] = None,
    event_queue = None
):
    """
    Wrap White Agent's tools to use fixtures.
    
    Args:
        white_agent_instance: Instance of WhiteAgent from chatbot.agent
        controller: Green Agent controller
        use_fixtures: Whether to use fixtures
        trace_ledger: Optional trace ledger manager for recording tool calls
        event_queue: Optional event queue for streaming events
    """
    # Reset tracking for new execution
    reset_tool_call_tracking()
    
    if not use_fixtures:
        return
    
    from .streaming.event_queue import get_event_queue
    
    interceptor = ToolInterceptor(controller, use_fixtures=use_fixtures)
    
    # Store interceptor reference for later access
    white_agent_instance._tool_interceptor = interceptor
    white_agent_instance._green_controller = controller
    white_agent_instance._trace_ledger = trace_ledger
    white_agent_instance._event_queue = event_queue or get_event_queue()  # Store event queue for intermediate steps
    
    # Set up ReAct callback handler for AgentExecutor
    try:
        from .streaming.react_callback import ReActCallbackHandler
        react_callback = ReActCallbackHandler(event_queue=white_agent_instance._event_queue)
        white_agent_instance.react_callback = react_callback
        
        # Update AgentExecutor to use callback handler
        # We need to recreate the executor with callbacks
        if hasattr(white_agent_instance, 'agent_executor'):
            # Store the original agent and tools
            original_agent = white_agent_instance.agent_executor.agent
            original_tools = white_agent_instance.agent_executor.tools
            
            from langchain.agents import AgentExecutor
            white_agent_instance.agent_executor = AgentExecutor(
                agent=original_agent,
                tools=original_tools,
                verbose=True,
                max_iterations=8,  # Reduced from 15 to prevent excessive retries (allows 2 per tool across 4 tools)
                max_execution_time=300,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
                callbacks=[react_callback],  # Add callback handler
                early_stopping_method="force"  # Stop forcefully when max iterations reached
            )
            logger.info("[Integration] ReAct callback handler added to AgentExecutor")
    except Exception as e:
        logger.warning(f"[Integration] Failed to set up ReAct callback handler: {e}", exc_info=True)
    
    # Monkey-patch tools in place to use fixtures
    # This avoids recreating the agent executor
    if hasattr(white_agent_instance, 'tools'):
        for tool in white_agent_instance.tools:
            if not use_fixtures:
                continue
            
            # Store original methods
            original_run = tool._run
            original_arun = tool._arun
            tool_name = tool.name
            
            # Create wrapper function with captured variables
            fixture_wrapper_ref = interceptor.fixture_wrapper
            controller_ref = controller
            trace_ledger_ref = trace_ledger
            
            def make_wrapped_run(orig_run, orig_arun, t_name):
                def wrapped_run(query: str) -> str:
                    logger.info(f"[Integration] Tool {t_name} called with query: {query}")
                    
                    # Check for duplicate calls (max 2 attempts per tool+query combination)
                    should_block, attempt_count, failure_reason = check_and_increment_tool_call(t_name, query)
                    
                    if should_block:
                        if failure_reason and "Permanent failure" in failure_reason:
                            error_msg = (
                                f"PERMANENT_FAILURE: Tool '{t_name}' has permanently failed. "
                                f"{failure_reason}. Cannot proceed with this tool."
                            )
                        else:
                            error_msg = (
                                f"Error: Tool '{t_name}' has already been called {attempt_count} times with similar parameters. "
                                f"Previous attempts did not succeed. Please use a different approach or acknowledge this limitation."
                            )
                        logger.warning(f"[Integration] Blocking duplicate tool call: {t_name} - {failure_reason}")
                        
                        # Still record in trace ledger for visibility
                        if trace_ledger_ref:
                            try:
                                trace_ledger_ref.record_tool_call(
                                    tool_name=t_name,
                                    arguments={'query': query},
                                    return_value=error_msg,
                                    execution_time_ms=0,
                                    error="Duplicate call blocked"
                                )
                            except:
                                pass
                        
                        return error_msg
                    
                    start_time = time.time()
                    args = {'query': query}
                    
                    try:
                        # Use fixture wrapper to get fixture or call original
                        if fixture_wrapper_ref:
                            logger.info(f"[Integration] Using fixture wrapper for {t_name}")
                            # Create a simple callable that just takes query
                            def original_callable(q):
                                logger.info(f"[Integration] Original callable called for {t_name}")
                                return orig_run(q)
                            
                            # Wrap it - this will emit events and return fixture if available
                            wrapped_func = fixture_wrapper_ref.wrap_tool(t_name, original_callable)
                            logger.info(f"[Integration] Calling wrapped function for {t_name}")
                            result = wrapped_func(query)
                            
                            # Get raw DataFrame/JSON data from fixture wrapper (stored in _last_fixture_data)
                            raw_data = None
                            if fixture_wrapper_ref:
                                # fixture_wrapper_ref IS the FixtureWrapper instance, access _last_fixture_data directly
                                last_fixture = getattr(fixture_wrapper_ref, '_last_fixture_data', None)
                                if last_fixture is not None:
                                    raw_data = last_fixture
                                    logger.info(f"[Integration] Retrieved raw data from fixture wrapper: {type(raw_data).__name__}")
                            
                            # Fallback: try to get from intercepted calls if not found
                            if raw_data is None:
                                intercepted_calls = fixture_wrapper_ref.get_intercepted_calls() if fixture_wrapper_ref else []
                                if intercepted_calls:
                                    # Find the most recent call for this tool
                                    for call in reversed(intercepted_calls):
                                        if call.get('tool_name') == t_name:
                                            if 'raw_data' in call:
                                                raw_data = call['raw_data']
                                                logger.info(f"[Integration] Retrieved raw data from intercepted calls: {type(raw_data).__name__}")
                                            break
                            
                            logger.info(f"[Integration] Wrapped function returned result of length: {len(str(result)) if result else 0}")
                            logger.info(f"[Integration] Raw data captured: {type(raw_data).__name__ if raw_data is not None else 'None'}")
                        else:
                            logger.warning(f"[Integration] No fixture wrapper, calling original for {t_name}")
                            result = orig_run(query)
                        
                        execution_time = (time.time() - start_time) * 1000  # ms
                        
                        # Check if result indicates permanent failure
                        result_str = str(result) if result else ""
                        if "PERMANENT_FAILURE" in result_str or "permanent failure" in result_str.lower():
                            record_tool_failure(t_name, result_str)
                        else:
                            # Mark success to prevent further duplicate calls with same query
                            if result_str and not result_str.lower().startswith("error"):
                                record_tool_success(t_name, query, result_str)
                        
                        # Record in trace ledger if available - store raw DataFrame/JSON if available
                        if trace_ledger_ref:
                            try:
                                # Use raw_data if available (DataFrame/JSON), otherwise use result (string)
                                record_value = raw_data if raw_data is not None else result
                                trace_ledger_ref.record_tool_call(
                                    tool_name=t_name,
                                    arguments=args,
                                    return_value=record_value,  # Store raw DataFrame/JSON structure
                                    execution_time_ms=execution_time
                                )
                                logger.info(f"[Integration] Tool call recorded in trace ledger with {type(record_value).__name__}")
                            except Exception as e:
                                logger.warning(f"Failed to record tool call in trace ledger: {e}", exc_info=True)
                        
                        return result
                    except Exception as e:
                        execution_time = (time.time() - start_time) * 1000
                        error_msg = str(e)
                        
                        # Record error in trace ledger
                        if trace_ledger_ref:
                            try:
                                trace_ledger_ref.record_tool_call(
                                    tool_name=t_name,
                                    arguments=args,
                                    return_value=None,
                                    execution_time_ms=execution_time,
                                    error=error_msg
                                )
                            except:
                                pass
                        
                        raise
                
                async def wrapped_arun(query: str):
                    # For async, call wrapped_run
                    return wrapped_run(query)
                
                return wrapped_run, wrapped_arun
            
            # Replace methods
            tool._run, tool._arun = make_wrapped_run(original_run, original_arun, tool_name)


def create_green_agent_for_evaluation(
    seed: Optional[int] = None,
    scenario_id: Optional[str] = None,
    use_fixtures: bool = True
) -> NewGreenAgent:
    """
    Create a new Green Agent instance for evaluation.
    
    Args:
        seed: Seed for deterministic execution
        scenario_id: Scenario identifier
        use_fixtures: Whether to use fixtures
        
    Returns:
        Green Agent instance
    """
    return NewGreenAgent(
        seed=seed,
        scenario_id=scenario_id,
        use_fixtures=use_fixtures,
        disable_network=use_fixtures
    )


def intercept_tool_calls_for_display(
    white_agent_instance,
    controller: GreenAgentController
) -> List[Dict[str, Any]]:
    """
    Get intercepted tool calls for UI display.
    
    Args:
        white_agent_instance: White Agent instance
        controller: Green Agent controller
        
    Returns:
        List of intercepted tool calls with parameters and fixture responses
    """
    # Access interceptor if it exists
    if hasattr(white_agent_instance, '_tool_interceptor'):
        interceptor = white_agent_instance._tool_interceptor
        return interceptor.get_intercepted_calls()
    
    return []

