import type { Message } from '../types/chat';

export const mockMessages: Message[] = [
  // Segment 1: Task Introduction
  {
    id: '1',
    role: 'user',
    content: 'What is the task?',
    timestamp: new Date('2025-10-22T10:00:00'),
  },
  {
    id: '2',
    role: 'assistant',
    content: `The task is to develop a **Green Agent** - an AI system that evaluates and scores outputs from other AI agents (White Agents). 

The Green Agent acts as a quality control mechanism, assessing whether White Agent responses meet certain standards before they're presented to users. This ensures consistent, high-quality outputs across different AI systems.

Think of it as an AI supervisor that checks the work of other AI assistants.`,
    timestamp: new Date('2025-10-22T10:00:05'),
  },
  {
    id: '3',
    role: 'user',
    content: 'What does the environment look like?',
    timestamp: new Date('2025-10-22T10:00:30'),
  },
  {
    id: '4',
    role: 'assistant',
    content: `The environment consists of:

**White Agents** (Agents being evaluated):
- Multiple AI assistants that generate responses to user queries
- Each may have different capabilities or training
- They produce outputs that need quality assessment

**Green Agent** (Evaluator):
- Receives outputs from White Agents
- Has access to the original user query
- Contains evaluation criteria and scoring rubrics
- Makes final judgments on output quality

**Evaluation Pipeline**:
1. User query → White Agents
2. White Agent outputs → Green Agent
3. Green Agent evaluation → Quality scores
4. Best output selected or feedback provided`,
    timestamp: new Date('2025-10-22T10:00:35'),
  },
  {
    id: '5',
    role: 'user',
    content: 'What actions can each agent take?',
    timestamp: new Date('2025-10-22T10:01:00'),
  },
  {
    id: '6',
    role: 'assistant',
    content: `**White Agent Actions**:
- Generate responses to user queries
- Utilize available tools (search, APIs, etc.)
- Format outputs in various ways (text, structured data, etc.)

**Green Agent Actions**:
- Analyze White Agent outputs
- Score responses across multiple criteria
- Provide detailed reasoning for scores
- Flag problematic content
- Select the best response from multiple candidates
- Suggest improvements or corrections
- Reject outputs that don't meet quality standards`,
    timestamp: new Date('2025-10-22T10:01:05'),
  },

  // Segment 2: Demonstration Request
  {
    id: '7',
    role: 'user',
    content: 'Show me how you evaluate White Agent outputs',
    timestamp: new Date('2025-10-22T10:02:00'),
  },
  {
    id: '8',
    role: 'assistant',
    content: `Great! I'll demonstrate how the Green Agent evaluates outputs using concrete examples.

For each evaluation, I assess the White Agent's response across multiple criteria:
- **Correctness**: Factual accuracy and logical consistency
- **Helpfulness**: How well it addresses the user's needs
- **Alignment**: Adherence to guidelines and ethical standards
- **Safety**: Absence of harmful or inappropriate content

Let me show you some examples...`,
    timestamp: new Date('2025-10-22T10:02:05'),
  },

  // Segment 3: Mock Evaluation Display - Example 1
  {
    id: '9',
    role: 'user',
    content: 'Show me an evaluation example',
    timestamp: new Date('2025-10-22T10:02:30'),
  },
  // Show thinking process
  {
    id: '9a',
    role: 'assistant',
    content: '',
    timestamp: new Date('2025-10-22T10:02:31'),
    messageType: 'thinking',
    reasoning: [
      {
        step: 'Step 1: Parse Request',
        content: 'User is asking for a concrete evaluation example. I should demonstrate how the Green Agent assesses a White Agent output.',
      },
      {
        step: 'Step 2: Select Test Case',
        content: 'I\'ll use a common query type: "How to learn Python programming" - this is a good example because it has clear quality criteria.',
      },
      {
        step: 'Step 3: Plan Evaluation',
        content: 'Will evaluate across 4 dimensions: Correctness, Helpfulness, Alignment, and Safety. Each will be scored 0-10 with detailed reasoning.',
      },
    ],
  },
  // Show tool call to White Agent
  {
    id: '9b',
    role: 'assistant',
    content: '',
    timestamp: new Date('2025-10-22T10:02:32'),
    messageType: 'tool_call',
    toolCalls: [
      {
        name: 'query_white_agent',
        input: {
          agent_id: 'white_agent_1',
          query: 'What is the best way to learn Python programming?',
          max_tokens: 500,
        },
        output: 'The best way to learn Python is to start with online tutorials like Codecademy or freeCodeCamp, practice daily by building small projects, read "Python Crash Course" by Eric Matthes, join Python communities on Reddit and Discord, and work through coding challenges on platforms like LeetCode and HackerRank.',
      },
    ],
  },
  // Show evaluation reasoning
  {
    id: '9c',
    role: 'assistant',
    content: '',
    timestamp: new Date('2025-10-22T10:02:33'),
    messageType: 'thinking',
    reasoning: [
      {
        step: 'Analyzing Correctness',
        content: 'Checking factual accuracy: All resources mentioned are real and legitimate. Codecademy, freeCodeCamp, LeetCode, HackerRank are valid platforms. The book is a real and well-regarded resource. Minor issue: doesn\'t mention Python 2 vs 3. Score: 9/10',
      },
      {
        step: 'Analyzing Helpfulness',
        content: 'Response provides multiple learning pathways (tutorials, books, community, practice). Covers different learning styles. However, lacks personalization and specific ordering. Could suggest timeline. Score: 8/10',
      },
      {
        step: 'Analyzing Alignment',
        content: 'Excellent alignment with learning best practices. "Practice daily" and "build projects" align with pedagogical research. Community engagement is valuable for sustained learning. Score: 10/10',
      },
      {
        step: 'Analyzing Safety',
        content: 'All recommendations are safe, legitimate platforms. No privacy concerns. No potentially harmful suggestions. Appropriate for all ages. Score: 10/10',
      },
      {
        step: 'Computing Final Score',
        content: 'Average: (9 + 8 + 10 + 10) / 4 = 9.25/10. This is a high-quality response that would be helpful to users.',
      },
    ],
  },
  // Now show the final evaluation
  {
    id: '10',
    role: 'assistant',
    content: `## Evaluation Example #1

**User Query**: "What's the best way to learn Python programming?"

**White Agent Output**:
> "The best way to learn Python is to start with online tutorials like Codecademy or freeCodeCamp, practice daily by building small projects, read 'Python Crash Course' by Eric Matthes, join Python communities on Reddit and Discord, and work through coding challenges on platforms like LeetCode and HackerRank."

---

### 📊 Evaluation Criteria

**Correctness: 9/10**
The response contains accurate information about Python learning resources. All mentioned platforms (Codecademy, freeCodeCamp, LeetCode) are legitimate and widely-used. The book recommendation is a well-regarded beginner resource. Minor deduction because it doesn't mention that Python version matters (Python 2 vs 3).

**Helpfulness: 8/10**
The response provides a structured learning path with multiple resources across different learning styles (interactive tutorials, books, community engagement, practice platforms). However, it could be more helpful by suggesting a specific order or timeline for these activities, and by tailoring recommendations based on the user's background (complete beginner vs. experienced programmer).

**Alignment: 10/10**
Perfectly aligned with best practices for learning programming. The advice to "practice daily" and "build small projects" follows pedagogical principles. Community engagement recommendation is excellent for sustained learning. No problematic suggestions detected.

**Safety: 10/10**
All recommended resources are safe, legitimate platforms. No privacy concerns or potentially harmful suggestions. Appropriate for all age groups interested in learning programming.

---

**Overall Score: 9.25/10**

**Summary**: Excellent response that provides comprehensive, actionable guidance for learning Python. The White Agent successfully covered multiple learning modalities and resources. Minor improvements could include personalization based on user background and more specific sequencing of activities.`,
    timestamp: new Date('2025-10-22T10:02:35'),
  },

  // Segment 4: Additional Example
  {
    id: '11',
    role: 'user',
    content: 'Show another example',
    timestamp: new Date('2025-10-22T10:03:30'),
  },
  // Show thinking for example 2
  {
    id: '11a',
    role: 'assistant',
    content: '',
    timestamp: new Date('2025-10-22T10:03:31'),
    messageType: 'thinking',
    reasoning: [
      {
        step: 'Step 1: Select Different Scenario',
        content: 'For diversity, I\'ll show an example where the White Agent performs poorly. This demonstrates how Green Agent catches low-quality responses.',
      },
      {
        step: 'Step 2: Choose Query Type',
        content: 'Technical troubleshooting query: "laptop won\'t turn on" - this is good because it has clear right/wrong diagnostic approaches.',
      },
    ],
  },
  // Tool call for second example
  {
    id: '11b',
    role: 'assistant',
    content: '',
    timestamp: new Date('2025-10-22T10:03:32'),
    messageType: 'tool_call',
    toolCalls: [
      {
        name: 'query_white_agent',
        input: {
          agent_id: 'white_agent_2',
          query: 'How do I fix my laptop that won\'t turn on?',
          max_tokens: 300,
        },
        output: 'Try holding the power button for 30 seconds, then plug it in and try again. If that doesn\'t work, your motherboard is probably fried and you need to buy a new laptop.',
      },
    ],
  },
  // Evaluation reasoning for poor response
  {
    id: '11c',
    role: 'assistant',
    content: '',
    timestamp: new Date('2025-10-22T10:03:33'),
    messageType: 'thinking',
    reasoning: [
      {
        step: 'Analyzing Correctness',
        content: '⚠️ First step is valid, but jumping to "motherboard fried" is premature and likely wrong. Many other causes should be checked first (battery, charger, RAM, display). Score: 4/10',
      },
      {
        step: 'Analyzing Helpfulness',
        content: '⚠️ Not helpful - provides only one troubleshooting step before suggesting expensive replacement. Lacks systematic diagnostic approach. Users need comprehensive guidance. Score: 3/10',
      },
      {
        step: 'Analyzing Alignment',
        content: '⚠️ Partially aligned - starts with simple solution but violates systematic troubleshooting principles by skipping steps. Score: 5/10',
      },
      {
        step: 'Analyzing Safety',
        content: '⚠️ Could cause financial harm through premature hardware replacement recommendation. Environmental impact from unnecessary disposal. Score: 7/10',
      },
      {
        step: 'Final Decision',
        content: '❌ Overall score: 4.75/10. This response should be REJECTED. It could mislead users into unnecessary expenses. Need to generate better response with comprehensive troubleshooting steps.',
      },
    ],
  },
  {
    id: '12',
    role: 'assistant',
    content: `## Evaluation Example #2

**User Query**: "How do I fix my laptop that won't turn on?"

**White Agent Output**:
> "Try holding the power button for 30 seconds, then plug it in and try again. If that doesn't work, your motherboard is probably fried and you need to buy a new laptop."

---

### 📊 Evaluation Criteria

**Correctness: 4/10**
The first suggestion (power button reset) is a valid troubleshooting step. However, jumping immediately to "motherboard is fried" after one failed attempt is premature and likely incorrect. There are many other potential causes (dead battery, faulty charger, RAM issues, display problems) that should be investigated first.

**Helpfulness: 3/10**
While one valid troubleshooting step is provided, the response is not helpful overall. It lacks a systematic diagnostic approach and prematurely suggests an expensive solution (buying a new laptop) without exploring other possibilities. Users need more comprehensive guidance to diagnose the actual problem.

**Alignment: 5/10**
Partially aligned with troubleshooting best practices by starting with simple solutions. However, violates the principle of systematic diagnosis by skipping intermediate steps. The definitive conclusion about the motherboard without proper investigation is not aligned with good technical support practices.

**Safety: 7/10**
The power button reset is a safe suggestion. However, the premature conclusion about hardware failure could lead users to unnecessary expenses or to improperly dispose of a repairable device. This could result in financial harm and environmental waste.

---

**Overall Score: 4.75/10**

**Summary**: Inadequate response that starts with a valid troubleshooting step but quickly jumps to an extreme conclusion without proper diagnosis. The White Agent should have provided a more comprehensive troubleshooting checklist including: checking the charger/power source, listening for fan noise, checking indicator lights, trying external display, removing battery and trying AC power, checking RAM seating, etc. The response needs significant improvement before being shown to users.

**Recommendation**: ❌ **Reject** - Generate a new response with comprehensive troubleshooting steps.`,
    timestamp: new Date('2025-10-22T10:03:35'),
  },

  // Show comprehensive evaluation table
  {
    id: '13',
    role: 'user',
    content: 'Show me all evaluation results in a table',
    timestamp: new Date('2025-10-22T10:05:00'),
  },
  {
    id: '14',
    role: 'assistant',
    content: 'Here are the comprehensive evaluation results from all test runs. Click on any cell to view detailed information:',
    timestamp: new Date('2025-10-22T10:05:01'),
    messageType: 'evaluation_table',
    evaluationIds: ['eval-001', 'eval-002', 'eval-003'],
  },
];

