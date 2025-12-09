<!-- 0e5776ab-4b58-494e-a440-88e64f1de8a6 8d1ee5ba-b6dd-4ac8-96c5-22461543a976 -->
# Fix Duplicate Tool Calls and Expose DataFrame/JSON Operations

## Problem Summary

1. **Duplicate Tool Calls**: White Agent processes same message twice (once directly, once via Green Agent)
2. **Missing DataFrame/JSON Visibility**: Raw data structures are captured but not streamed to UI
3. **Missing ReAct Operations**: Internal AgentExecutor reasoning steps not visible

## Solution Architecture

### Layer 1: Fix Duplicate Execution

**File**: `backend/api_server.py`

**Change**: Remove direct White Agent call, let Green Agent handle orchestration

- **Line 331**: Remove `result = await white_agent.process_message(message_data["message"])`
- **Line 353**: Use result from Green Agent instead: `result = eval_result.get("white_agent_output")`
- Green Agent already calls White Agent internally, so we only need one execution path

### Layer 2: Capture and Stream AgentExecutor Intermediate Steps

**File**: `backend/chatbot/agent.py`

**Current Issue**: Intermediate steps stored in state but not emitted

**Changes**:

1. **Lines 483-496**: Enhance intermediate step capture to emit events

   - For each intermediate step, emit `tool_call_step` event with:
     - Tool name
     - Tool input
     - Raw output (DataFrame/JSON before string conversion)
     - Output type (DataFrame/JSON/string)
   - Access event queue via WhiteAgent instance

2. **Access Pattern**: 

   - Store event queue reference in WhiteAgent `__init__`
   - Pass event queue from `integration.py` when wrapping tools
   - Emit events synchronously via queue

**File**: `backend/green_agent/integration.py`

**Changes**:

1. **Line 143**: Pass event queue to WhiteAgent for intermediate step emission
2. Store event queue reference in WhiteAgent for access during AgentExecutor execution

### Layer 3: Capture ReAct Loop Operations

**File**: `backend/chatbot/agent.py`

**Challenge**: AgentExecutor's internal ReAct loop not directly accessible

**Solution**: Use LangChain callbacks to intercept ReAct operations

1. **Create Custom Callback Handler**:

   - Implement `AsyncCallbackHandler` from LangChain
   - Capture: `on_llm_start`, `on_tool_start`, `on_tool_end`, `on_agent_action`
   - Emit events for each ReAct step (Thought, Action, Observation)

2. **Integration**:

   - **Line 150-155**: Add callback handler to AgentExecutor
   - Handler emits events via event queue for:
     - LLM reasoning steps
     - Tool call attempts
     - Tool outputs (with raw data)
     - Final observations

**File**: `backend/green_agent/streaming/react_callback.py` (NEW)

**Create**: Callback handler that captures ReAct operations and emits events

### Layer 4: Preserve Raw Data Through Pipeline

**File**: `backend/green_agent/tools/fixture_wrapper.py`

**Current Issue**: Line 177 converts DataFrame to JSON string, losing structure

**Changes**:

1. **Lines 170-192**: Modify return strategy

   - Store raw DataFrame/JSON in `_last_fixture_data` (already exists)
   - Return string for AgentExecutor (required)
   - But ensure `intermediate_steps` gets raw data

**File**: `backend/green_agent/integration.py`

**Changes**:

1. **Lines 73-74**: After wrapped function call, extract raw data from fixture wrapper
2. **Line 105**: Use raw data (DataFrame/JSON) in trace ledger, not string
3. Pass raw data through to intermediate steps capture

**File**: `backend/chatbot/agent.py`

**Changes**:

1. **Lines 487-493**: When processing intermediate steps, check if raw data exists
2. If tool output is string but raw data available, use raw data
3. Store both: string (for LLM) and raw (for display)

### Layer 5: Stream DataFrame Operations

**File**: `backend/chatbot/tools.py`

**Challenge**: `python_repl_ast` tool executes DataFrame operations internally

**Solution**: Wrap `python_repl_ast` to capture operations

1. **Modify `PythonREPLTool` wrapper**:

   - Intercept code execution
   - Parse executed code to identify DataFrame operations
   - Emit events showing:
     - Code executed
     - DataFrame shape/columns before/after
     - Data preview (head/tail)
     - Operation type (filter, transform, aggregate)

2. **Event Format**:
   ```python
   {
     'type': 'dataframe_operation',
     'tool_name': 'python_repl_ast',
     'code': 'df.info()',
     'operation': 'info',
     'dataframe_snapshot': {...},  # Shape, columns, sample rows
   }
   ```


## Implementation Steps

### Step 1: Fix Duplicate Calls (30 min)

- Remove line 331 in `api_server.py`
- Modify line 353 to extract result from Green Agent
- Test: Should see 3 tool calls (not 6)

### Step 2: Capture Intermediate Steps (1 hour)

- Add event queue reference to WhiteAgent
- Modify intermediate step capture to emit events
- Test: Intermediate steps appear in UI trace

### Step 3: Add ReAct Callback (1.5 hours)

- Create `react_callback.py`
- Integrate with AgentExecutor
- Test: ReAct steps visible in UI

### Step 4: Preserve Raw Data (1 hour)

- Fix fixture wrapper to preserve raw data
- Update integration to pass raw data through
- Test: DataFrames/JSON visible in trace ledger

### Step 5: Capture DataFrame Operations (1 hour)

- Wrap `python_repl_ast` to capture operations
- Emit dataframe_operation events
- Test: DataFrame operations visible in UI

## Testing Checklist

- [ ] Tool calls appear once (not duplicated)
- [ ] Intermediate steps stream in real-time
- [ ] Raw DataFrame structures visible in trace
- [ ] Raw JSON structures visible in trace
- [ ] ReAct reasoning steps (Thought/Action/Observation) visible
- [ ] DataFrame operations (df.info, df.shape, etc.) visible
- [ ] All data structures preserved through pipeline

## Files to Modify

1. `backend/api_server.py` - Remove duplicate White Agent call
2. `backend/chatbot/agent.py` - Add intermediate step emission, callback handler
3. `backend/green_agent/integration.py` - Pass event queue, preserve raw data
4. `backend/green_agent/tools/fixture_wrapper.py` - Improve raw data preservation
5. `backend/green_agent/streaming/react_callback.py` - NEW: ReAct callback handler
6. `backend/chatbot/tools.py` - Wrap python_repl_ast for operation capture

## Estimated Time

Total: 4-5 hours

### To-dos

- [ ] Create fixture system with seeded data for flights, hotels, restaurants, weather
- [ ] Wrap tools to use fixtures instead of real APIs with strict schemas
- [ ] Create tool registry with whitelist and minimal args validation
- [ ] Implement sandbox with no network, deterministic seed, tool call logging
- [ ] Create plan validator that accepts only JSON, validates structure and tools
- [ ] Implement safe normalizations (whitespace, dates, arrows, markdown)
- [ ] Create deterministic tool runner that executes validated plans
- [ ] Implement append-only trace ledger recording all tool calls
- [ ] Create schema validation for white agent submissions
- [ ] Implement grounding checks for all concrete claims
- [ ] Create feasibility checker for weather, sold-out, visa constraints
- [ ] Implement timing realism checks (overlaps, buffers, daily caps)
- [ ] Create geo-logistics validator for routes and lodging proximity
- [ ] Implement personalization checks against traveler brief
- [ ] Create budget validator with cost recomputation and comparison
- [ ] Implement clarity and evidence quality scoring
- [ ] Implement NDCG@K calculation for lodging ranking
- [ ] Create stability scorer with seeded perturbation testing
- [ ] Build scoring orchestrator that coordinates all scoring components
- [ ] Create seed management system for deterministic execution
- [ ] Implement isolation system with reset and clean state
- [ ] Create artifact generator for metrics, leaderboard, traces
- [ ] Build test suite with unit tests, fuzz tests, reproducibility tests
- [ ] Create main GreenAgent orchestrator coordinating all layers
- [ ] Integrate with existing codebase and add backward compatibility