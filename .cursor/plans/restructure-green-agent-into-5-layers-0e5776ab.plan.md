---
name: Fix Duplicate Tool Calls and Expose DataFrame/JSON Operations
overview: ""
todos:
  - id: c281d252-b7c2-4200-a91f-dc36ef342068
    content: Create fixture system with seeded data for flights, hotels, restaurants, weather
    status: pending
  - id: efd73382-961c-47dd-b24e-14facb4ef6fd
    content: Wrap tools to use fixtures instead of real APIs with strict schemas
    status: pending
  - id: 70042f65-4831-43a0-af63-400dc418e556
    content: Create tool registry with whitelist and minimal args validation
    status: pending
  - id: 9aa5b9b6-b310-401d-adb4-a203d0b65ee9
    content: Implement sandbox with no network, deterministic seed, tool call logging
    status: pending
  - id: 6d9b0f88-d001-464c-82e6-ebb54ab04020
    content: Create plan validator that accepts only JSON, validates structure and tools
    status: pending
  - id: 7fd29cca-13d8-44dd-952d-d3bb71c550f9
    content: Implement safe normalizations (whitespace, dates, arrows, markdown)
    status: pending
  - id: dc6e1e19-0e3b-49c1-942c-6dde1ef2f985
    content: Create deterministic tool runner that executes validated plans
    status: pending
  - id: 2eebca5b-7d2c-4bd7-920d-7664ef561d3a
    content: Implement append-only trace ledger recording all tool calls
    status: pending
  - id: 299cbd4e-e190-47d2-b885-e04ed71436ad
    content: Create schema validation for white agent submissions
    status: pending
  - id: bd4df1e9-b4d0-4a7e-9c9b-7297627dff77
    content: Implement grounding checks for all concrete claims
    status: pending
  - id: 17049b56-1b10-4aab-9989-2f5159fad62b
    content: Create feasibility checker for weather, sold-out, visa constraints
    status: pending
  - id: ab420824-2355-4c4b-b926-56beecee8e48
    content: Implement timing realism checks (overlaps, buffers, daily caps)
    status: pending
  - id: d3cbf577-f3e0-47ec-9963-d930a3e482ee
    content: Create geo-logistics validator for routes and lodging proximity
    status: pending
  - id: 019d0f44-abe3-4c4e-8678-aebcc069c357
    content: Implement personalization checks against traveler brief
    status: pending
  - id: c4a6a537-d602-4b51-a851-f9f17bd563a4
    content: Create budget validator with cost recomputation and comparison
    status: pending
  - id: 19720a05-8204-42f7-bd96-1881f6be11a0
    content: Implement clarity and evidence quality scoring
    status: pending
  - id: ef413cbf-61a8-4b02-9c90-80da16320101
    content: Implement NDCG@K calculation for lodging ranking
    status: pending
  - id: eeacf45d-c335-4b15-8bfc-162ad4c0bffa
    content: Create stability scorer with seeded perturbation testing
    status: pending
  - id: e0131f71-0f47-4ebc-9519-fc4c2f1f40c8
    content: Build scoring orchestrator that coordinates all scoring components
    status: pending
  - id: f80da1de-6cfd-4de5-a49b-34d1240143db
    content: Create seed management system for deterministic execution
    status: pending
  - id: c9d92114-7d99-412a-9c1b-7e8eb93205dd
    content: Implement isolation system with reset and clean state
    status: pending
  - id: 7db80edf-c86b-4cb5-bc38-2787c521f2b2
    content: Create artifact generator for metrics, leaderboard, traces
    status: pending
  - id: 5f7ba349-8f18-4692-9356-2db358c09989
    content: Build test suite with unit tests, fuzz tests, reproducibility tests
    status: pending
  - id: 39aecd46-29e9-4e02-9f90-d85d53c154df
    content: Create main GreenAgent orchestrator coordinating all layers
    status: pending
  - id: bd95ac65-e71b-46a1-8685-b89b55c652c8
    content: Integrate with existing codebase and add backward compatibility
    status: pending
---

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