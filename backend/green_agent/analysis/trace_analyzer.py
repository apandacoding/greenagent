"""LLM-based backend logs analyzer."""
import json
import logging
from typing import Dict, Any, Optional, List
import anthropic
import os
from dotenv import load_dotenv
import subprocess
from pathlib import Path
import sys

load_dotenv()

logger = logging.getLogger(__name__)

# Function schema for structured trace analysis
TRACE_ANALYSIS_SCHEMA = {
    "name": "analyze_trace_ledger",
    "description": "Analyze a trace ledger and extract structured information about tool calls, DataFrame operations, and actions performed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "High-level summary of what happened in this trace ledger"
            },
            "tool_calls": {
                "type": "array",
                "description": "List of all tool calls made",
                "items": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the tool called"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Why this tool was called and what it was meant to accomplish"
                        },
                        "key_parameters": {
                            "type": "object",
                            "description": "Key parameters/arguments passed to the tool"
                        },
                        "result_summary": {
                            "type": "string",
                            "description": "Summary of what the tool returned"
                        }
                    },
                    "required": ["tool_name", "purpose"]
                }
            },
            "dataframe_operations": {
                "type": "array",
                "description": "DataFrame operations performed (from python_repl_ast calls)",
                "items": {
                    "type": "object",
                    "properties": {
                        "operation_type": {
                            "type": "string",
                            "description": "Type of operation (e.g., 'filter', 'sort', 'aggregate', 'transform')"
                        },
                        "dataframe_name": {
                            "type": "string",
                            "description": "Name of the dataframe being operated on"
                        },
                        "operation": {
                            "type": "string",
                            "description": "The actual operation performed (e.g., 'sort_values', 'groupby')"
                        },
                        "full_expression": {
                            "type": "string",
                            "description": "Full Python expression that was executed"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "What this operation was meant to accomplish"
                        }
                    },
                    "required": ["operation_type", "operation"]
                }
            },
            "analysis_steps": {
                "type": "array",
                "description": "High-level analysis steps performed",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_number": {
                            "type": "integer",
                            "description": "Sequential step number"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what happened in this step"
                        },
                        "tools_used": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tools used in this step"
                        },
                        "dataframe_ops": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "DataFrame operations in this step"
                        }
                    },
                    "required": ["step_number", "description"]
                }
            },
            "key_insights": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key insights about the data processing and analysis performed"
            },
            "detailed_actions": {
                "type": "array",
                "description": "Detailed action-by-action breakdown with inputs, observations, and DataFrame operations",
                "items": {
                    "type": "object",
                    "properties": {
                        "action_number": {
                            "type": "integer",
                            "description": "Sequential action number"
                        },
                        "thought": {
                            "type": "string",
                            "description": "The Thought that preceded this action"
                        },
                        "action": {
                            "type": "string",
                            "description": "The action taken (e.g., 'python_repl_ast', 'flight_search')"
                        },
                        "action_input": {
                            "type": "string",
                            "description": "The full input/code that was executed"
                        },
                        "observation": {
                            "type": "string",
                            "description": "The observation/result from the action"
                        },
                        "dataframe_functions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "DataFrame functions/methods called (e.g., 'df.shape', 'df.sort_values()')"
                        },
                        "dataframe_columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "DataFrame columns accessed or mentioned"
                        },
                        "dataframe_name": {
                            "type": "string",
                            "description": "Name of the dataframe variable used (e.g., 'df', 'filtered_df')"
                        }
                    },
                    "required": ["action_number", "action"]
                }
            }
        },
        "required": ["summary", "tool_calls", "dataframe_operations", "analysis_steps", "detailed_actions"]
    }
}


def get_recent_backend_logs(lines: int = 500) -> str:
    """
    Get recent backend logs by reading from log file or using tail/grep.
    
    Args:
        lines: Number of recent lines to retrieve
        
    Returns:
        Recent log output as string
    """
    try:
        # Try multiple log file locations
        possible_log_files = [
            Path(__file__).parent.parent.parent / "backend" / "backend.log",
            Path.cwd() / "backend.log",
            Path.cwd() / "backend" / "backend.log",
        ]
        
        log_file = None
        for log_path in possible_log_files:
            if log_path.exists():
                log_file = log_path
                break
        
        if log_file:
            # Read last N lines from log file
            try:
                result = subprocess.run(
                    ["tail", "-n", str(lines), str(log_file)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    logger.info(f"Successfully read {len(result.stdout)} chars from {log_file}")
                    return result.stdout
            except FileNotFoundError:
                # tail command not available, read file directly
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        all_lines = f.readlines()
                        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        content = ''.join(recent_lines)
                        logger.info(f"Successfully read {len(content)} chars from {log_file} (direct read)")
                        return content
                except Exception as e:
                    logger.warning(f"Failed to read log file directly: {e}")
        
        # Fallback: try to grep process logs if running
        try:
            # Try to get logs from running uvicorn process
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "uvicorn" in result.stdout or "api_server" in result.stdout:
                logger.info("Uvicorn process found, but cannot access stdout directly")
        except:
            pass
        
        logger.warning(f"Backend log file not found in any of: {possible_log_files}")
        return ""
        
    except Exception as e:
        logger.error(f"Error reading backend logs: {e}", exc_info=True)
        return ""


def extract_agent_executor_logs(log_content: str) -> str:
    """
    Extract AgentExecutor-related log entries from backend logs.
    Looks for Thought/Action/Observation patterns and DataFrame operations.
    """
    lines = log_content.split('\n')
    agent_lines = []
    
    # Patterns to identify AgentExecutor messages
    patterns = [
        'Thought:',
        'Action:',
        'Action Input:',
        'Observation:',
        'Entering new AgentExecutor chain',
        'Finished chain',
        'I now know the final answer',
        'Final Answer:',
        'python_repl_ast',
        'df.shape',
        'df.columns',
        'df.sort_values',
        'df.filter',
        'df.groupby',
        'df.merge',
        'df.copy',
        'df.head',
        'df.tail',
        'df.describe',
        'df.info',
        'df.value_counts',
        'df.iterrows',
        'df.loc',
        'df.iloc',
        'Running FlightSearchTool',
        'Running HotelSearchTool',
        'Running RestaurantSearchTool',
        '🏨',  # Hotel emoji
        '🍴',  # Restaurant emoji
        '✈️',  # Flight emoji
        'hotel_search',
        'restaurant_search',
        'flight_search',
        'AgentExecutor returned output',
        'Intermediate steps',
        'ReActCallback',
        'chat_node',  # Hotel/restaurant tools use chat_node
        'Making hotel search request',
        'Making restaurant search request',
    ]
    
    # Track if we're in an AgentExecutor chain
    in_chain = False
    collected_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Start collecting when we enter an AgentExecutor chain
        if 'entering new agentexecutor chain' in line_lower:
            in_chain = True
            collected_lines = []
        
        # Check if line contains any relevant pattern
        if any(pattern.lower() in line_lower for pattern in patterns):
            collected_lines.append(line)
            # Also include a few lines of context before/after
            if i > 0 and lines[i-1] not in collected_lines:
                # Add previous line if it's relevant
                prev_line = lines[i-1]
                if any(keyword in prev_line.lower() for keyword in ['agent', 'tool', 'df.', 'action', 'thought']):
                    collected_lines.insert(-1, prev_line)
            if i < len(lines) - 1:
                next_line = lines[i+1]
                if any(keyword in next_line.lower() for keyword in ['agent', 'tool', 'df.', 'observation']):
                    if next_line not in collected_lines:
                        collected_lines.append(next_line)
        
        # Also collect DataFrame-related lines
        if 'df.' in line or 'dataframe' in line_lower or 'pd.' in line:
            if line not in collected_lines:
                collected_lines.append(line)
        
        # Stop collecting after "Finished chain" or "Final Answer"
        if 'finished chain' in line_lower or 'final answer:' in line_lower:
            in_chain = False
            if collected_lines:
                agent_lines.extend(collected_lines)
                agent_lines.append('')  # Add separator
                collected_lines = []
    
    # If we have collected lines from active chain, add them
    if collected_lines:
        agent_lines.extend(collected_lines)
    
    # Return the extracted logs, prioritizing more recent entries
    if agent_lines:
        # Get last 500 lines of relevant content
        return '\n'.join(agent_lines[-500:])
    else:
        # Fallback: return last portion of logs that might contain relevant info
        return '\n'.join(lines[-500:])


def analyze_backend_logs(log_lines: int = 20000, tool_filter: Optional[str] = None, known_tools: Optional[set] = None) -> Dict[str, Any]:
    """
    Analyze backend logs using LLM to extract structured information about
    AgentExecutor actions, tool calls, and DataFrame operations.
    
    Args:
        log_lines: Number of recent log lines to analyze
        tool_filter: Optional tool name to filter logs for (e.g., 'hotel_search', 'flight_search')
                    If None, analyzes all tools and returns results grouped by tool
        known_tools: Optional set of tool names from trace ledger (more reliable than log parsing)
        
    Returns:
        If tool_filter is provided: Structured analysis for that specific tool
        If tool_filter is None: Dict with keys as tool names, values as analysis results
    """
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment")
            return {"error": "API key not configured"}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Get recent backend logs
        logger.info(f"Reading last {log_lines} lines from backend logs...")
        all_logs = get_recent_backend_logs(lines=log_lines)
        
        if not all_logs:
            return {"error": "Could not retrieve backend logs. Make sure backend.log exists or logs are accessible."}
        
        # If tool_filter is provided, we'll filter from raw logs first, then extract
        # This ensures we capture the right AgentExecutor chain for the tool
        used_relevant_section = False
        if tool_filter:
            # Filter raw logs first to find the relevant section
            tool_lower = tool_filter.lower()
            tool_markers = {
                'flight_search': [
                    '✈️ running flightsearchtool',
                    'running flightsearchtool',
                    'flightsearchtool',
                    'running flight_search'
                ],
                'hotel_search': [
                    '🏨 running hotelsearchtool',
                    'running hotelsearchtool',
                    'hotelsearchtool',
                    'making hotel search request',
                    'running hotel_search'
                ],
                'restaurant_search': [
                    '🍴 running restaurantsearchtool',
                    'running restaurantsearchtool',
                    'restaurantsearchtool',
                    'making restaurant search request',
                    'running restaurant_search'
                ]
            }
            markers = tool_markers.get(tool_filter, [tool_lower])
            
            # Find the tool execution in raw logs
            raw_lines = all_logs.split('\n')
            tool_start_idx = None
            
            # CRITICAL FIX: Search from the BOTTOM up to find the MOST RECENT execution
            # This prevents picking up old/cached runs from earlier in the logs
            for i in range(len(raw_lines) - 1, -1, -1):
                line = raw_lines[i]
                line_lower = line.lower()
                for marker in markers:
                    if marker.lower() in line_lower:
                        tool_start_idx = i
                        logger.info(f"Found {tool_filter} tool execution at line {i} (scanning from bottom)")
                        break
                if tool_start_idx is not None:
                    break
            
            # If not found, try expanding the log window once
            if tool_start_idx is None and log_lines < 30000:
                logger.info(f"No marker found for {tool_filter} with {log_lines} lines. Expanding to 30000 lines.")
                all_logs = get_recent_backend_logs(lines=30000)
                raw_lines = all_logs.split('\n')
                # Try search again from bottom
                for i in range(len(raw_lines) - 1, -1, -1):
                    line = raw_lines[i]
                    line_lower = line.lower()
                    for marker in markers:
                        if marker.lower() in line_lower:
                            tool_start_idx = i
                            logger.info(f"Found {tool_filter} tool execution at line {i} after expansion")
                            break
                    if tool_start_idx is not None:
                        break
            
            # If we found the tool, extract a window around it (forward only)
            if tool_start_idx is not None:
                # Get context starting from the tool marker going forward
                # We don't need much before, but we need enough after to capture the chain
                start = max(0, tool_start_idx - 10) 
                end = min(len(raw_lines), tool_start_idx + 2500) # Increased window size
                relevant_section = '\n'.join(raw_lines[start:end])
                logger.info(f"Extracted {end - start} lines starting at {tool_filter} execution")
                
                # Now extract AgentExecutor logs from this section
                agent_logs = extract_agent_executor_logs(relevant_section)
                used_relevant_section = True
                logger.info(f"After extraction for {tool_filter}, agent_logs chars: {len(agent_logs)}")
                
                if len(agent_logs) < 100:
                     logger.warning(f"AgentExecutor logs extracted for {tool_filter} seem too short ({len(agent_logs)} chars).")
            else:
                logger.warning(f"Tool marker not found for {tool_filter} in raw logs.")
                # CRITICAL FIX: Do NOT fallback to general extraction if tool marker not found.
                # Returning general logs (which likely contain OTHER tools) causes incorrect analysis.
                return {"error": f"No logs found for tool {tool_filter} in the last {log_lines} lines."}
        else:
            # Extract AgentExecutor-related logs
            agent_logs = extract_agent_executor_logs(all_logs)
        
        if not agent_logs:
            logger.warning("No AgentExecutor logs found in recent backend output")
            return {"error": "No AgentExecutor activity found in logs"}
        
        # If tool_filter is provided and we already used a relevant section, skip further filtering
        if tool_filter and used_relevant_section:
            logger.info(f"Using extracted section directly for {tool_filter} (skipping secondary filtering)")
        elif tool_filter:
            # We should not reach here if used_relevant_section is False because we return early above
            pass
        
        logger.info(f"Extracted {len(agent_logs)} characters of AgentExecutor logs")
        
        # If no tool_filter, we need to analyze all tools and group by tool
        # First, identify all tools in the logs
        if not tool_filter:
            # Start with known tools from trace ledger (most reliable)
            tool_names = set(known_tools) if known_tools else set()
            logger.info(f"Starting with known tools from trace ledger: {tool_names}")
            
            # Also extract tool names from logs (look for "Running XTool" or "Action: X")
            # This is a fallback/complement to trace ledger
            lines = agent_logs.split('\n')
            
            # Debug: log sample lines to understand what we're seeing
            sample_lines = [l for l in lines if any(keyword in l.lower() for keyword in ['running', 'action:', 'hotel', 'restaurant', 'flight'])]
            logger.info(f"Sample log lines with tool keywords ({len(sample_lines)} found): {sample_lines[:10]}")
            
            for line in lines:
                line_lower = line.lower()
                # Check for "Running XTool" pattern (with or without emoji prefix)
                if 'running' in line_lower:
                    # Extract tool name from "Running FlightSearchTool" or "Running HotelSearchTool"
                    # Handle emoji prefixes (✈️, 🏨, 🍴) and case variations
                    if 'flightsearchtool' in line_lower or 'flight_search' in line_lower or ('flight' in line_lower and 'search' in line_lower):
                        tool_names.add('flight_search')
                    elif 'hotelsearchtool' in line_lower or 'hotel_search' in line_lower or ('hotel' in line_lower and 'search' in line_lower):
                        tool_names.add('hotel_search')
                    elif 'restaurantsearchtool' in line_lower or 'restaurant_search' in line_lower or ('restaurant' in line_lower and 'search' in line_lower):
                        tool_names.add('restaurant_search')
                
                # Also check for explicit tool calls in Action lines
                if 'action:' in line_lower:
                    if 'flight_search' in line_lower:
                        tool_names.add('flight_search')
                    elif 'hotel_search' in line_lower:
                        tool_names.add('hotel_search')
                    elif 'restaurant_search' in line_lower:
                        tool_names.add('restaurant_search')
                
                # Also check for tool names in ReActCallback or other log patterns
                if 'reactcallback' in line_lower or 'agent action' in line_lower:
                    if 'flight_search' in line_lower:
                        tool_names.add('flight_search')
                    elif 'hotel_search' in line_lower:
                        tool_names.add('hotel_search')
                    elif 'restaurant_search' in line_lower:
                        tool_names.add('restaurant_search')
            
            logger.info(f"Tools detected (from logs + trace ledger): {tool_names}")
            if not tool_names:
                logger.warning("No tools detected. Checking raw logs for tool patterns...")
                # Fallback: check raw logs too
                raw_lines = all_logs.split('\n')
                for line in raw_lines[-500:]:  # Check last 500 lines of raw logs
                    line_lower = line.lower()
                    if 'flight_search' in line_lower or ('flight' in line_lower and 'search' in line_lower and 'tool' in line_lower):
                        tool_names.add('flight_search')
                    if 'hotel_search' in line_lower or ('hotel' in line_lower and 'search' in line_lower and 'tool' in line_lower):
                        tool_names.add('hotel_search')
                    if 'restaurant_search' in line_lower or ('restaurant' in line_lower and 'search' in line_lower and 'tool' in line_lower):
                        tool_names.add('restaurant_search')
                logger.info(f"After checking raw logs, tools detected: {tool_names}")
            
            # If we have known tools from ledger but no logs found, still analyze them
            if known_tools and not tool_names:
                logger.info(f"Using known tools from trace ledger since no tools found in logs: {known_tools}")
                tool_names = known_tools
            
            # If we found multiple tools, analyze each separately
            if len(tool_names) > 1:
                logger.info(f"Found {len(tool_names)} tools in logs: {tool_names}. Analyzing each separately...")
                results_by_tool = {}
                for tool_name in tool_names:
                    try:
                        logger.info(f"Analyzing tool: {tool_name}")
                        tool_analysis = analyze_backend_logs(log_lines=log_lines, tool_filter=tool_name, known_tools=known_tools)
                        if tool_analysis and 'error' not in tool_analysis:
                            results_by_tool[tool_name] = tool_analysis
                            logger.info(f"Successfully analyzed {tool_name}")
                        else:
                            logger.warning(f"Analysis for {tool_name} returned error or empty result: {tool_analysis}")
                            results_by_tool[tool_name] = tool_analysis or {"error": "Empty analysis result"}
                    except Exception as e:
                        logger.error(f"Error analyzing tool {tool_name}: {e}", exc_info=True)
                        results_by_tool[tool_name] = {"error": str(e)}
                logger.info(f"Completed analysis for {len(results_by_tool)} tools: {list(results_by_tool.keys())}")
                return results_by_tool
            # If only one tool or no tools found, continue with single analysis
            elif len(tool_names) == 1:
                tool_filter = list(tool_names)[0]
                logger.info(f"Single tool detected: {tool_filter}. Analyzing...")
            else:
                logger.warning("No tools detected. Proceeding with general analysis...")
        
        # Build prompt - identify which tool we're analyzing
        tool_context = f" for the '{tool_filter}' tool" if tool_filter else ""
        
        # Add DataFrame context hints based on tool
        df_context_hint = ""
        if tool_filter == "hotel_search":
            df_context_hint = "\n- The DataFrame contains HOTEL data (columns like: name, hotel_class, overall_rating, night_lowest, total_lowest, location_rating, amenities, etc.)"
        elif tool_filter == "flight_search":
            df_context_hint = "\n- The DataFrame contains FLIGHT data (columns like: pair_id, total_price, airline, from_out, to_out, depart_time_out, arrive_time_out, duration_min_out, layovers_out, from_ret, to_ret, depart_time_ret, arrive_time_ret, duration_min_ret, layovers_ret, etc.)"
        elif tool_filter == "restaurant_search":
            df_context_hint = "\n- The DataFrame contains RESTAURANT data (columns like: name, rating, price, address, cuisine, etc.)"
        
        prompt = f"""Analyze the following backend logs from an AI agent system{tool_context}. The logs contain AgentExecutor messages showing Thought/Action/Observation cycles, tool calls, and DataFrame operations.

IMPORTANT: 
- Focus on the MOST RECENT execution chains{tool_context if tool_filter else ""}
- Look for complete Thought/Action/Observation cycles{df_context_hint}
- Identify the DataFrame context correctly - for hotel_search, look for hotel data; for flight_search, look for flight data; for restaurant_search, look for restaurant data
- DO NOT confuse DataFrames from different tools - only analyze DataFrame operations that are relevant to {tool_filter if tool_filter else "the current tool"}

Backend Logs:
{agent_logs[-8000:]}

Please analyze these logs and extract structured information about:
1. What tools were called and why (from "Action:" and tool execution messages)
2. What DataFrame operations were performed (from python_repl_ast calls with df.shape, df.sort_values, df.filter, etc.)
3. The sequence of analysis steps (Thought → Action → Observation cycles)
4. Key insights about the data processing workflow
5. **CRITICAL**: Extract detailed action-by-action breakdown with:
   - Each Thought/Action/Observation cycle from the MOST RECENT execution
   - The exact action_input (COMPLETE code/query executed) for EACH action
   - The observation/result returned for EACH action (COMPLETE output)
   - All DataFrame functions called (df.shape, df.columns, df.sort_values, df.filter, df.groupby, etc.)
   - DataFrame column names accessed
   - DataFrame variable names used (df, filtered_df, etc.)

Focus on:
- Identifying ALL DataFrame operations like df.shape, df.sort_values(), df.filter(), df.groupby(), aggregations, transformations, etc.
- Extracting the COMPLETE action_input code for each python_repl_ast call (everything between "Action Input:" and "Observation:")
- Capturing the COMPLETE observation/result text (everything after "Observation:" until the next "Action" or "Thought")
- Identifying ALL DataFrame column names mentioned in the code
- Understanding the purpose of each operation from the Thought/Action context
- Describing the overall data analysis workflow
- Highlighting key transformations and insights

Look for patterns like:
- "Action: python_repl_ast"
- "Action Input:" followed by Python code (may span multiple lines)
- "Observation:" followed by results/output
- "Thought:" messages explaining the reasoning
- DataFrame column names in the code (df['column_name'], df.column_name, etc.)
- Tool execution messages like "Running FlightSearchTool"
- "Final Answer:" sections showing successful completions

For each action in the detailed_actions array:
- Extract the COMPLETE action_input (ALL the code/query between Action Input and Observation, including multi-line code)
- Extract the COMPLETE observation (ALL the output/result, including multi-line outputs)
- List ALL df.* function calls (df.shape, df.columns.tolist(), df.sort_values(), df.filter(), etc.)
- List ALL column names referenced (from df['col'], df.col, or column lists)
- Include the Thought that preceded the action (if present)

Pay special attention to:
- Multiple python_repl_ast calls in sequence
- DataFrame transformations (filtering, sorting, aggregations)
- Column access patterns (df['column'], df.column, df[['col1', 'col2']])
- Data exploration steps (df.shape, df.info(), df.describe(), df.value_counts())
- Final successful outputs (after "Final Answer:")

Return your analysis using the analyze_trace_ledger function."""

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            tools=[TRACE_ANALYSIS_SCHEMA],
            tool_choice={"type": "tool", "name": "analyze_trace_ledger"},
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract tool use result
        if response.content and len(response.content) > 0:
            block = response.content[0]
            if hasattr(block, 'type') and block.type == 'tool_use':
                if hasattr(block, 'input'):
                    return block.input
            elif hasattr(block, 'text'):
                # Fallback: try to parse JSON from text
                try:
                    return json.loads(block.text)
                except:
                    pass
        
        return {"error": "Failed to extract analysis from LLM response"}
        
    except Exception as e:
        logger.error(f"Error analyzing backend logs: {e}", exc_info=True)
        return {"error": str(e)}


# Keep old function name for backwards compatibility
def analyze_trace_ledger(trace_ledger: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deprecated: Use analyze_backend_logs() instead.
    This function now redirects to analyze backend logs.
    """
    return analyze_backend_logs()


def get_trace_summary_text(trace_ledger: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary text from trace ledger.
    Useful for logging or display.
    """
    traces = trace_ledger.get("traces", [])
    if not traces:
        return "No traces found in ledger."
    
    summary_parts = [
        f"Trace Ledger Analysis ({len(traces)} traces)",
        "=" * 50
    ]
    
    # Group by tool
    tool_groups = {}
    for trace in traces:
        tool_name = trace.get("tool_name", "unknown")
        if tool_name not in tool_groups:
            tool_groups[tool_name] = []
        tool_groups[tool_name].append(trace)
    
    for tool_name, tool_traces in tool_groups.items():
        summary_parts.append(f"\n{tool_name} ({len(tool_traces)} calls):")
        for trace in tool_traces:
            if trace.get("df_operations"):
                ops = trace["df_operations"]
                summary_parts.append(f"  - DataFrame operations: {len(ops)}")
                for op in ops[:3]:  # Show first 3
                    summary_parts.append(f"    • {op.get('dataframe', 'df')}.{op.get('operation', 'op')}")
    
    return "\n".join(summary_parts)
