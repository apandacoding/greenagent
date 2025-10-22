# Frontend Hardcoded Chat Plan - Green Agent Evaluation Demo

## Background
**Green Agent** is an AI evaluator that assesses outputs from White Agents (AI models being tested).

### Agent Roles
- **Green Agent**: Evaluator - orchestrates evaluation and scores outputs
- **User Agent**: Orchestrator - bridges Green and White agents, runs tasks
- **White Agent**: Evaluated AI - produces outputs to be assessed

### Evaluation Process Flow
1. Green Agent calls User Agent to run evaluation
2. User Agent (background) calls White Agent with task description
3. White Agent generates output
4. User Agent feeds output back to Green Agent
5. Green Agent evaluates output and produces report

---

## Chat Flow Segments

### Segment 1: Introduction - Understanding Green Agent
**User**: "What is your role as Green Agent?"
**Green Agent**: Explains role as evaluator, quality control for AI outputs

**User**: "What environment do you operate in?"
**Green Agent**: Describes the multi-agent environment with Green, User, and White agents

**User**: "What agents do you have access to?"
**Green Agent**: Details the three agent types and their responsibilities:
- **Green Agent (Self)**: Evaluation and scoring
- **User Agent**: Task orchestration and execution
- **White Agent**: AI models being evaluated (GPT-4, Claude, etc.)

---

### Segment 2: Demonstration Request
**User**: "Show me how you evaluate AI outputs"
**Green Agent**: Introduction to evaluation process with step-by-step overview

---

### Segment 3: Live Evaluation Demo

#### Step 1: Initiating Evaluation
**User**: "Run an evaluation"
**Green Agent Message**: "Starting evaluation process. Calling User Agent to execute task..."
**Green Agent Tool Call**: 
```json
{
  "tool": "call_user_agent",
  "input": {
    "task_id": "code_review_task",
    "white_agents": ["gpt-4", "claude-3.5"]
  }
}
```

#### Step 2: User Agent Execution (Background)
**Green Agent Message**: "User Agent is executing task on White Agents..."
**Green Agent Reasoning Trace**:
- "User Agent received task: Code Review Task"
- "Calling White Agent: GPT-4..."
- "Calling White Agent: Claude-3.5..."
- "Collecting outputs from all White Agents"

#### Step 3: Output Reception
**Green Agent Message**: "Received outputs from White Agents via User Agent. Beginning evaluation..."
**Green Agent Reasoning Trace**:
- "Parsing output from GPT-4"
- "Parsing output from Claude-3.5"
- "Preparing evaluation criteria"

#### Step 4: Evaluation Process
**Green Agent Message**: "Evaluating outputs across multiple criteria..."
**Green Agent Reasoning Trace**:
- "Criterion 1: Correctness - Checking factual accuracy..."
- "Criterion 2: Helpfulness - Assessing user value..."
- "Criterion 3: Code Quality - Reviewing best practices..."
- "Criterion 4: Safety - Checking for issues..."
- "Computing aggregated scores..."

#### Step 5: Final Report
**Green Agent Message**: "Evaluation complete. Here's the summary report:"

---

## Final Report Format

### Metrics Table Component
Interactive table with 4 columns:

| Task Name + Title | Models Used | Scenario | Aggregated Score |
|-------------------|-------------|----------|------------------|
| Code Review: Python Function | GPT-4, Claude-3.5 | Review quality... | 8.5/10 ⭐ |
| Bug Detection: React Component | GPT-4, Claude-3.5 | Find errors... | 7.2/10 ⭐ |
| API Documentation: REST Endpoints | GPT-4, Claude-3.5 | Generate docs... | 9.1/10 ⭐ |

**All cells are clickable and open a right-side panel**

---

## Interactive Panel System (Manus Computer Style)

### Panel 1: Task Name/Title Click
Shows detailed task description:
```
Task ID: code_review_task_001
Task Name: Code Review
Title: Python Function Optimization

Full Description:
Review the following Python function for:
- Code efficiency
- Readability
- Best practices
- Potential bugs
[... full task text ...]
```

### Panel 2: Scenario Click
Shows detailed scenario with agent traces:
```
Scenario: Code Review Task

=== User Agent → White Agent Trace ===
[10:00:01] User Agent: Calling GPT-4...
[10:00:01] → Sending task to GPT-4
[10:00:03] ← Received response from GPT-4

[10:00:03] User Agent: Calling Claude-3.5...
[10:00:03] → Sending task to Claude-3.5
[10:00:05] ← Received response from Claude-3.5

=== White Agent Outputs ===

--- GPT-4 Output ---
[Full output from GPT-4]

--- Claude-3.5 Output ---
[Full output from Claude-3.5]
```

### Panel 3: Aggregated Score Click
Shows score breakdown from each evaluation run:
```
Aggregated Score: 8.5/10

=== Run #1: GPT-4 ===
Correctness: 9/10
Helpfulness: 8/10
Code Quality: 9/10
Safety: 10/10
Overall: 9.0/10

=== Run #2: Claude-3.5 ===
Correctness: 8/10
Helpfulness: 8/10
Code Quality: 8/10
Safety: 9/10
Overall: 8.25/10

=== Aggregation Method ===
Average: (9.0 + 8.25) / 2 = 8.625/10
Rounded: 8.5/10

=== Detailed Reasoning ===
[Green Agent's evaluation reasoning for each criterion]
```

---

## Frontend Components to Build

### 1. Chat Components (Existing)
- [x] ChatMessage - basic messages
- [x] ToolCallDisplay - show tool calls
- [x] ReasoningDisplay - show reasoning traces

### 2. New Table Components
- [x] **MetricsTable** - Main evaluation results table
- [x] **TableRow** - Clickable row with 4 columns (integrated in MetricsTable)
- [x] **TableCell** - Clickable cell component (integrated in MetricsTable)

### 3. New Panel Components
- [x] **SidePanel** - Slide-in panel (Manus style)
- [x] **TaskDetailPanel** - Shows full task description
- [x] **ScenarioPanel** - Shows agent traces and outputs
- [x] **ScoreBreakdownPanel** - Shows detailed scoring

### 4. Layout Components
- [x] **Panel State Management** - Integrated in ChatContainer
- [x] **Panel Routing** - Click handlers connected to panel system

---

## Implementation Phases

### Phase 1: Chat Flow ✅ COMPLETED
- ✅ Basic agent messages
- ✅ Tool call displays
- ✅ Reasoning traces

### Phase 2: Metrics Table ✅ COMPLETED
- ✅ Create table structure
- ✅ Add hardcoded evaluation data (3 evaluations)
- ✅ Make cells clickable
- ✅ Handle click events (console.log for now)

### Phase 3: Side Panel System ✅ COMPLETED
- ✅ Create slide-in panel component (SidePanel)
- ✅ Implement TaskDetailPanel
- ✅ Implement ScenarioPanel with agent traces
- ✅ Implement ScoreBreakdownPanel with progress bars
- ✅ Add smooth transitions and animations
- ✅ Handle panel open/close state
- ✅ Connect to table click events

### Phase 4: Integration & Polish 🔄 IN PROGRESS
- ✅ Connect table clicks to panels
- ✅ Multiple evaluation examples (3 tasks)
- [ ] Update mock messages with comprehensive flow
- [ ] Polish styling and UX
- [ ] Test full demo flow

