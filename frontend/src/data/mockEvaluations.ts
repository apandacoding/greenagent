import type { EvaluationResult } from '../types/evaluation';

export const mockEvaluations: EvaluationResult[] = [
  {
    id: 'eval-001',
    taskName: 'Code Review',
    title: 'Python Function Optimization',
    modelsUsed: ['GPT-4', 'Claude-3.5'],
    scenarioSummary: 'Review code quality, efficiency, and best practices',
    aggregatedScore: 8.5,
    taskDetail: {
      taskId: 'code_review_task_001',
      taskName: 'Code Review',
      title: 'Python Function Optimization',
      fullDescription: `Review the following Python function for:
- Code efficiency and performance
- Readability and maintainability
- Adherence to best practices (PEP 8)
- Potential bugs or edge cases
- Security considerations

Function to review:
\`\`\`python
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
\`\`\`

Provide specific suggestions for improvement.`,
    },
    scenarioDetail: {
      description: 'Code review task with multiple AI models evaluating the same Python function.',
      agentTraces: [
        { timestamp: '10:00:01', agent: 'User Agent', action: 'Task received from Green Agent' },
        { timestamp: '10:00:01', agent: 'User Agent', action: 'Calling GPT-4 with task', direction: 'send' },
        { timestamp: '10:00:03', agent: 'User Agent', action: 'Response received from GPT-4', direction: 'receive' },
        { timestamp: '10:00:03', agent: 'User Agent', action: 'Calling Claude-3.5 with task', direction: 'send' },
        { timestamp: '10:00:05', agent: 'User Agent', action: 'Response received from Claude-3.5', direction: 'receive' },
        { timestamp: '10:00:05', agent: 'User Agent', action: 'Sending results to Green Agent', direction: 'send' },
      ],
      whiteAgentOutputs: [
        {
          agentName: 'GPT-4',
          timestamp: '10:00:03',
          output: `Code Review for process_data function:

**Issues Identified:**
1. Using range(len(data)) is not Pythonic - use enumerate or direct iteration
2. List concatenation with append in loop is fine but could use list comprehension
3. No input validation - what if data is None or empty?
4. No type hints for better code clarity

**Suggested Improvements:**
\`\`\`python
def process_data(data: list[int | float]) -> list[int | float]:
    """Process positive numbers by doubling them.
    
    Args:
        data: List of numbers to process
        
    Returns:
        List containing doubled positive numbers
    """
    if not data:
        return []
    return [num * 2 for num in data if num > 0]
\`\`\`

**Benefits:**
- More concise and readable
- Type hints improve code clarity
- Input validation prevents errors
- List comprehension is more Pythonic and slightly faster`,
        },
        {
          agentName: 'Claude-3.5',
          timestamp: '10:00:05',
          output: `Python Function Review:

**Current Issues:**
1. Anti-pattern: range(len(data)) - should iterate directly
2. Missing docstring and type annotations
3. No error handling for edge cases
4. Could be more concise with list comprehension

**Refactored Version:**
\`\`\`python
def process_data(data: list[float | int] | None) -> list[float | int]:
    """Double all positive values in the input list.
    
    Args:
        data: List of numeric values (or None)
        
    Returns:
        New list with positive values doubled
        
    Example:
        >>> process_data([1, -2, 3, 0, 4])
        [2, 6, 8]
    """
    if data is None:
        return []
    
    return [value * 2 for value in data if value > 0]
\`\`\`

**Improvements Made:**
- Added comprehensive docstring with example
- Type hints for better IDE support
- None check for robustness
- Pythonic list comprehension
- More efficient O(n) single pass`,
        },
      ],
    },
    scoreBreakdown: {
      runs: [
        {
          agentName: 'GPT-4',
          criteria: [
            {
              criterion: 'Correctness',
              score: 9,
              maxScore: 10,
              reasoning: 'Identified all major issues correctly. The suggested code is functionally correct and handles edge cases properly.',
            },
            {
              criterion: 'Helpfulness',
              score: 8,
              maxScore: 10,
              reasoning: 'Provided clear explanations and a concrete refactored example. Could have included more edge case discussion.',
            },
            {
              criterion: 'Code Quality',
              score: 9,
              maxScore: 10,
              reasoning: 'Excellent suggestions following PEP 8 and Python best practices. List comprehension usage is appropriate.',
            },
            {
              criterion: 'Safety',
              score: 10,
              maxScore: 10,
              reasoning: 'Suggested defensive programming with input validation. No security concerns introduced.',
            },
          ],
          overallScore: 9.0,
        },
        {
          agentName: 'Claude-3.5',
          criteria: [
            {
              criterion: 'Correctness',
              score: 8,
              maxScore: 10,
              reasoning: 'Good identification of issues. The refactored code is correct but the None check might be overly defensive.',
            },
            {
              criterion: 'Helpfulness',
              score: 8,
              maxScore: 10,
              reasoning: 'Very helpful with docstring example showing input/output. Clear structure and explanations.',
            },
            {
              criterion: 'Code Quality',
              score: 8,
              maxScore: 10,
              reasoning: 'Good quality suggestions. The docstring is excellent. Minor: complexity comment not needed for O(n).',
            },
            {
              criterion: 'Safety',
              score: 9,
              maxScore: 10,
              reasoning: 'Excellent None handling. Very defensive approach prevents runtime errors.',
            },
          ],
          overallScore: 8.25,
        },
      ],
      aggregatedScore: 8.5,
      aggregationMethod: 'Average of both runs: (9.0 + 8.25) / 2 = 8.625, rounded to 8.5',
      detailedReasoning: `Both models provided high-quality code reviews with practical suggestions. GPT-4 had slightly better analysis of edge cases and cleaner refactoring. Claude-3.5 excelled in documentation with the docstring example. Both correctly identified the anti-pattern of using range(len()) and suggested list comprehensions. Overall, these are production-ready reviews.`,
    },
  },
  {
    id: 'eval-002',
    taskName: 'Bug Detection',
    title: 'React Component Error Finding',
    modelsUsed: ['GPT-4', 'Claude-3.5'],
    scenarioSummary: 'Identify bugs in React component with state management issues',
    aggregatedScore: 7.2,
    taskDetail: {
      taskId: 'bug_detection_task_002',
      taskName: 'Bug Detection',
      title: 'React Component Error Finding',
      fullDescription: `Find all bugs and potential issues in this React component:

\`\`\`jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetch('/api/users/' + userId)
      .then(res => res.json())
      .then(data => setUser(data));
  }, []);
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>Email: {user.email}</p>
    </div>
  );
}
\`\`\`

Identify all bugs, runtime errors, and best practice violations.`,
    },
    scenarioDetail: {
      description: 'Bug detection in React component with missing dependencies and error handling.',
      agentTraces: [
        { timestamp: '10:05:01', agent: 'User Agent', action: 'Task received from Green Agent' },
        { timestamp: '10:05:01', agent: 'User Agent', action: 'Calling GPT-4 with task', direction: 'send' },
        { timestamp: '10:05:04', agent: 'User Agent', action: 'Response received from GPT-4', direction: 'receive' },
        { timestamp: '10:05:04', agent: 'User Agent', action: 'Calling Claude-3.5 with task', direction: 'send' },
        { timestamp: '10:05:07', agent: 'User Agent', action: 'Response received from Claude-3.5', direction: 'receive' },
        { timestamp: '10:05:07', agent: 'User Agent', action: 'Sending results to Green Agent', direction: 'send' },
      ],
      whiteAgentOutputs: [
        {
          agentName: 'GPT-4',
          timestamp: '10:05:04',
          output: `Bugs Found:

1. **Missing dependency in useEffect** - userId not in dependency array
2. **No null check before rendering** - will crash on initial render
3. **No error handling** - fetch can fail silently
4. **Missing cleanup** - no abort controller for unmounted component`,
        },
        {
          agentName: 'Claude-3.5',
          timestamp: '10:05:07',
          output: `Issues Detected:

1. **Runtime Error**: Accessing user.name before user is loaded (null pointer)
2. **Missing Dependency**: useEffect missing userId in deps
3. **No Loading State**: User sees error before data loads
4. **No Error Handling**: Network failures not handled`,
        },
      ],
    },
    scoreBreakdown: {
      runs: [
        {
          agentName: 'GPT-4',
          criteria: [
            {
              criterion: 'Correctness',
              score: 8,
              maxScore: 10,
              reasoning: 'Found all critical bugs. Mentioned cleanup but could be more specific about memory leak.',
            },
            {
              criterion: 'Completeness',
              score: 7,
              maxScore: 10,
              reasoning: 'Identified main issues but missed loading state UX problem.',
            },
            {
              criterion: 'Clarity',
              score: 7,
              maxScore: 10,
              reasoning: 'Clear explanations but could provide example fixes.',
            },
            {
              criterion: 'Helpfulness',
              score: 6,
              maxScore: 10,
              reasoning: 'Lists problems but lacks concrete solutions or code examples.',
            },
          ],
          overallScore: 7.0,
        },
        {
          agentName: 'Claude-3.5',
          criteria: [
            {
              criterion: 'Correctness',
              score: 8,
              maxScore: 10,
              reasoning: 'Correctly identified all major bugs including the critical runtime error.',
            },
            {
              criterion: 'Completeness',
              score: 8,
              maxScore: 10,
              reasoning: 'Good coverage including UX issue with loading state. Missed cleanup concern.',
            },
            {
              criterion: 'Clarity',
              score: 7,
              maxScore: 10,
              reasoning: 'Clear and concise. Good prioritization with "Runtime Error" label.',
            },
            {
              criterion: 'Helpfulness',
              score: 7,
              maxScore: 10,
              reasoning: 'Identifies problems clearly but no solution examples provided.',
            },
          ],
          overallScore: 7.5,
        },
      ],
      aggregatedScore: 7.2,
      aggregationMethod: 'Average: (7.0 + 7.5) / 2 = 7.25, rounded to 7.2',
      detailedReasoning: `Both models correctly identified the critical bugs. Claude-3.5 had slightly better coverage by noting the loading state UX issue. GPT-4 mentioned cleanup concerns. Both could improve by providing solution examples. These are adequate bug reports but lack the actionable detail for junior developers.`,
    },
  },
  {
    id: 'eval-003',
    taskName: 'API Documentation',
    title: 'REST Endpoints Documentation',
    modelsUsed: ['GPT-4', 'Claude-3.5'],
    scenarioSummary: 'Generate comprehensive API docs for REST endpoints',
    aggregatedScore: 9.1,
    taskDetail: {
      taskId: 'api_docs_task_003',
      taskName: 'API Documentation',
      title: 'REST Endpoints Documentation',
      fullDescription: `Generate documentation for these REST API endpoints:

POST /api/users
GET /api/users/:id
PUT /api/users/:id
DELETE /api/users/:id

Include: descriptions, parameters, request/response examples, status codes, and error handling.`,
    },
    scenarioDetail: {
      description: 'API documentation generation with comprehensive details and examples.',
      agentTraces: [
        { timestamp: '10:10:01', agent: 'User Agent', action: 'Task received from Green Agent' },
        { timestamp: '10:10:01', agent: 'User Agent', action: 'Calling GPT-4 with task', direction: 'send' },
        { timestamp: '10:10:06', agent: 'User Agent', action: 'Response received from GPT-4', direction: 'receive' },
        { timestamp: '10:10:06', agent: 'User Agent', action: 'Calling Claude-3.5 with task', direction: 'send' },
        { timestamp: '10:10:11', agent: 'User Agent', action: 'Response received from Claude-3.5', direction: 'receive' },
        { timestamp: '10:10:11', agent: 'User Agent', action: 'Sending results to Green Agent', direction: 'send' },
      ],
      whiteAgentOutputs: [
        {
          agentName: 'GPT-4',
          timestamp: '10:10:06',
          output: `# User API Documentation

## POST /api/users
Create a new user.

**Request Body:**
\`\`\`json
{
  "name": "John Doe",
  "email": "john@example.com"
}
\`\`\`

**Response (201):**
\`\`\`json
{
  "id": "123",
  "name": "John Doe",
  "email": "john@example.com"
}
\`\`\`

**Errors:**
- 400: Invalid input
- 409: Email already exists

[... similar detail for other endpoints ...]`,
        },
        {
          agentName: 'Claude-3.5',
          timestamp: '10:10:11',
          output: `# User Management API

## Create User
\`POST /api/users\`

Creates a new user account.

**Parameters:**
- name (string, required)
- email (string, required)

**Success Response (201 Created):**
\`\`\`json
{
  "id": "abc123",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "createdAt": "2025-10-22T10:10:06Z"
}
\`\`\`

[... comprehensive docs for all endpoints ...]`,
        },
      ],
    },
    scoreBreakdown: {
      runs: [
        {
          agentName: 'GPT-4',
          criteria: [
            {
              criterion: 'Completeness',
              score: 9,
              maxScore: 10,
              reasoning: 'Covered all endpoints with examples. Minor: missing rate limiting info.',
            },
            {
              criterion: 'Clarity',
              score: 9,
              maxScore: 10,
              reasoning: 'Very clear structure and formatting. Easy to follow.',
            },
            {
              criterion: 'Accuracy',
              score: 10,
              maxScore: 10,
              reasoning: 'All status codes and examples are technically correct.',
            },
            {
              criterion: 'Usability',
              score: 8,
              maxScore: 10,
              reasoning: 'Good but could include curl examples for developer convenience.',
            },
          ],
          overallScore: 9.0,
        },
        {
          agentName: 'Claude-3.5',
          criteria: [
            {
              criterion: 'Completeness',
              score: 10,
              maxScore: 10,
              reasoning: 'Excellent coverage including timestamps and all edge cases.',
            },
            {
              criterion: 'Clarity',
              score: 9,
              maxScore: 10,
              reasoning: 'Well-structured with clear parameter descriptions.',
            },
            {
              criterion: 'Accuracy',
              score: 9,
              maxScore: 10,
              reasoning: 'Accurate and includes helpful metadata like createdAt.',
            },
            {
              criterion: 'Usability',
              score: 9,
              maxScore: 10,
              reasoning: 'Very developer-friendly with detailed parameter info.',
            },
          ],
          overallScore: 9.25,
        },
      ],
      aggregatedScore: 9.1,
      aggregationMethod: 'Average: (9.0 + 9.25) / 2 = 9.125, rounded to 9.1',
      detailedReasoning: `Excellent documentation from both models. Claude-3.5 slightly edged ahead with more complete metadata and timestamps. Both provided professional-grade API docs that would be ready for production use. The formatting, examples, and error handling coverage were outstanding.`,
    },
  },
];

