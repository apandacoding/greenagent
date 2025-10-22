"""
Green Agent implementation using LangGraph for flight booking chatbot.
"""
import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from .models import AgentType, ChatMessage, ToolCall
from .tools import FlightTool, AnalysisTool
from .config import settings

logger = logging.getLogger(__name__)

class AgentState:
    """State for the Green Agent conversation"""
    def __init__(self):
        self.messages: List[ChatMessage] = []
        self.current_agent: AgentType = AgentType.USER
        self.tool_calls: List[ToolCall] = []
        self.conversation_id: str = ""
        self.created_at: datetime = datetime.now()

class GreenAgent:
    """Main Green Agent class using LangGraph for conversation flow"""
    
    def __init__(self):
        self.state = AgentState()
        self.flight_tool = FlightTool()
        self.analysis_tool = AnalysisTool()
        
        # Initialize LLMs
        self.anthropic_llm = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.7
        )
        
        self.openai_llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7
        )
        
        # Build the conversation graph
        self.graph = self._build_graph()

    # ---------------------------
    # Helpers for JSON tool plans
    # ---------------------------
    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract a single JSON object from free-text (tolerates code fences / extra prose).
        Returns None if no valid JSON object is found.
        """
        if not text:
            return None
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    def _get_latest_white_plan(self, state: 'AgentState') -> Optional[Dict[str, Any]]:
        """
        Parse the most recent WHITE_AGENT message as a tool plan:
        {
          "tool_plan_id": "...",
          "rationale": "...",
          "tool_calls": [
            { "id": "tc1", "tool": "flight_search"|"analysis", "args": { "query": "..." } }
          ]
        }
        """
        for msg in reversed(state.messages):
            if msg.agent_type == AgentType.WHITE_AGENT:
                plan = self._extract_json(msg.content)
                if plan and isinstance(plan, dict):
                    return plan
        return None

    def _get_latest_green_eval(self, state: 'AgentState') -> Optional[Dict[str, Any]]:
        """
        Parse the most recent GREEN_AGENT evaluation JSON:
        {
          "decision": "execute_tools" | "reject_plan",
          "issues": [...],
          "normalized_plan": { ... } | null
        }
        """
        for msg in reversed(state.messages):
            if msg.agent_type == AgentType.GREEN_AGENT:
                decision = self._extract_json(msg.content)
                if decision and isinstance(decision, dict) and "decision" in decision:
                    return decision
        return None
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("user_input", self._process_user_input)
        workflow.add_node("white_agent", self._white_agent_reasoning)
        workflow.add_node("green_agent", self._green_agent_evaluation)
        workflow.add_node("tool_execution", self._execute_tools)
        workflow.add_node("response_generation", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "white_agent")
        workflow.add_edge("white_agent", "green_agent")
        workflow.add_conditional_edges(
            "green_agent",
            self._should_use_tools,
            {
                "tools": "tool_execution",
                "response": "response_generation"
            }
        )
        workflow.add_edge("tool_execution", "response_generation")
        workflow.add_edge("response_generation", END)
        
        return workflow.compile()
    
    async def _process_user_input(self, state: AgentState) -> AgentState:
        """Process user input and determine intent"""
        logger.info("Processing user input")
        
        # Add user message to conversation
        user_message = ChatMessage(
            content=state.messages[-1].content if state.messages else "",
            agent_type=AgentType.USER,
            timestamp=datetime.now()
        )
        state.messages.append(user_message)
        
        return state
    
    async def _white_agent_reasoning(self, state: AgentState) -> AgentState:
        """White Agent reasoning and analysis"""
        logger.info("White Agent reasoning")
        
        # Get the latest user message
        user_message = state.messages[-1].content
        
        # Create reasoning prompt
        reasoning_prompt = (
        """
        You are the WHITE AGENT (Planner).
        Your *only* job is to translate the user's request into a deterministic TOOL PLAN for the GREEN AGENT to validate and execute.
        Do NOT answer the user. Do NOT include any prose outside of JSON. Output exactly one JSON object that follows the schema below.

        ## Allowed tools
        - "flight_search": Search for flights from natural-language instructions. 
            args: { "query": "<one concise sentence describing the search (routes, dates, constraints)>" }
            Example queries: "Cheapest round trip from OAK to EWR, depart 2025-11-07 return 2025-11-14, 1 adult economy", 
                            "Find nonstop SFO→JFK next Friday returning Sunday".
        - "analysis": Ask follow-up questions about the *already retrieved* flights, summarized by GREEN AGENT.
            args: { "query": "<analysis instruction over the current flight set>" }
            Example: "Among the returned options, which is the shortest total duration under $500?"

        ## Output schema (respond with JSON only)
        {
        "tool_plan_id": "<short id you generate>",
        "rationale": "<1–2 short sentences explaining why these tools are needed>",
        "tool_calls": [
            {
            "id": "tc1",
            "tool": "flight_search" | "analysis",
            "args": { "query": "<string>" }
            }
            // Additional calls are allowed if needed, in the order they should be executed.
        ]
        }

        ## Rules
        - If NO tool is necessary, set "tool_calls": [] and keep a brief "rationale".
        - Arguments must be minimal and concrete. Prefer explicit dates like "2025-11-07" over vague phrases. If the date cannot be resolved, keep the user's wording in the query.
        - Only use tools listed above. Do NOT invent tool names or arguments.
        - Do NOT include markdown fences or any text outside the single JSON object.

        ## Examples

        # Example A — user asks to find flights
        User: "Find me the cheapest OAK to EWR roundtrip Nov 7–14 in economy."
        Output:
        {
        "tool_plan_id": "b3b1e8",
        "rationale": "They want flight options; we should search flights by route and dates.",
        "tool_calls": [
            {
            "id": "tc1",
            "tool": "flight_search",
            "args": {
                "query": "Cheapest round trip OAK→EWR depart 2025-11-07 return 2025-11-14, 1 adult economy"
            }
            }
        ]
        }

        # Example B — user asks to compare or summarize already fetched results
        User: "Which of those is the shortest under $500?"
        Output:
        {
        "tool_plan_id": "7c0f21",
        "rationale": "They want a comparison over the current set of results.",
        "tool_calls": [
            {
            "id": "tc1",
            "tool": "analysis",
            "args": {
                "query": "Among the current options, shortest total duration under $500"
            }
            }
        ]
        }
        """
            + f"\nUser message: {user_message}\n"
            + "Now, generate ONLY the JSON object for this user's message."
        )
        
        # Get reasoning from LLM
        response = await self.anthropic_llm.ainvoke([HumanMessage(content=reasoning_prompt)])
        
        # Add reasoning to state
        reasoning_message = ChatMessage(
            content=response.content,
            agent_type=AgentType.WHITE_AGENT,
            timestamp=datetime.now()
        )
        state.messages.append(reasoning_message)
        
        return state
    
    async def _green_agent_evaluation(self, state: AgentState) -> AgentState:
        """Green Agent evaluation of White Agent's reasoning"""
        logger.info("Green Agent evaluation")
        
        # Get White Agent's reasoning
        white_agent_message = state.messages[-1].content
        
        # Strict, non-fabricating validator prompt (JSON-only output)
        evaluation_prompt = f"""
        You are the GREEN AGENT (Validator/Executor).

        Your responsibilities:
        1) Parse the WHITE AGENT’s JSON tool plan from the message above.
        2) Validate it against our rules (schema, allowed tools, safe args).
        3) Decide whether to execute tools. Never fabricate tool outputs or “assume” results.

        ## Allowed tools and args
        - flight_search: {{ "query": "<string>" }}
        - analysis:      {{ "query": "<string>" }}

        ## Validation rules
        - The plan must be a single JSON object with:
          - tool_plan_id: string
          - rationale: string (1–2 short sentences)
          - tool_calls: array of 0+ calls; each call has {{ id, tool, args }}
        - tool must be one of {{"flight_search","analysis"}} — reject others.
        - args must exist and must be a JSON object.
        - For our current tool interfaces, the only required arg is "query" (non-empty string).
        - You may apply SAFE NORMALIZATIONS only:
          - Trim whitespace.
          - Normalize unicode arrows to ASCII (e.g., "→" -> "->").
          - Preserve user-provided content exactly; do NOT invent dates, airports, prices, or counts.
        - Do NOT run tools if the plan is invalid or unsafe.

        ## Decision policy
        - If the plan is valid and has ≥1 tool call → decision="execute_tools".
        - If invalid or unknown tool/args → decision="reject_plan" with issues[].
        - If valid but needs trivial safe normalization → decision="execute_tools" and include normalized_plan.

        ## Output (JSON only)
        {{
          "decision": "execute_tools" | "reject_plan",
          "issues": ["<list of short strings>"],
          "normalized_plan": {{ ... }}  // Include only if you applied safe normalization; otherwise null.
        }}

        Never include tool outputs here. Do not fabricate any values. Return only the JSON object.

        WHITE AGENT MESSAGE:
        {white_agent_message}
        """
        
        # Get evaluation from LLM
        response = await self.anthropic_llm.ainvoke([HumanMessage(content=evaluation_prompt)])
        
        # Add evaluation to state
        evaluation_message = ChatMessage(
            content=response.content,
            agent_type=AgentType.GREEN_AGENT,
            timestamp=datetime.now()
        )
        state.messages.append(evaluation_message)
        
        return state
    
    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be used based on the Green evaluation (fallback to White plan)."""
        eval_json = self._get_latest_green_eval(state)
        if eval_json and eval_json.get("decision") == "execute_tools":
            return "tools"
        if eval_json and eval_json.get("decision") == "reject_plan":
            return "response"
        # Fallback: if White plan has tool_calls, proceed to tools.
        plan = self._get_latest_white_plan(state)
        if plan and isinstance(plan.get("tool_calls"), list) and len(plan["tool_calls"]) > 0:
            return "tools"
        return "response"
    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute necessary tools exactly as specified in the (normalized) White plan"""
        logger.info("Executing tools")
        
        eval_json = self._get_latest_green_eval(state) or {}
        if eval_json.get("decision") == "reject_plan":
            # Do not execute tools; leave tool_calls empty
            state.tool_calls = []
            return state
        
        normalized = eval_json.get("normalized_plan")
        plan = normalized if isinstance(normalized, dict) else (self._get_latest_white_plan(state) or {"tool_calls": []})
        tool_calls: List[ToolCall] = []
        
        for call in plan.get("tool_calls", []):
            tool_name = call.get("tool")
            args = call.get("args", {}) or {}
            query = args.get("query", "") if isinstance(args, dict) else ""
            status = "success"
            result: Dict[str, Any]
            
            try:
                if tool_name == "flight_search":
                    result = await self.flight_tool.execute(query)
                elif tool_name == "analysis":
                    result = await self.analysis_tool.execute(query)
                else:
                    status = "error"
                    result = {"status": "error", "message": f"Unknown tool '{tool_name}'"}
            except Exception as e:
                status = "error"
                result = {"status": "error", "message": str(e)}
            
            tool_calls.append(
                ToolCall(
                    name=tool_name or "unknown",
                    parameters={"query": query},
                    result=result,
                    status=result.get("status", status)
                )
            )
        
        state.tool_calls = tool_calls
        return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response"""
        logger.info("Generating response")
        
        # Combine all information for response generation
        user_message = state.messages[0].content
        white_agent_reasoning = state.messages[1].content
        green_agent_evaluation = state.messages[2].content
        
        # Include tool results if available
        tool_results = ""
        if state.tool_calls:
            tool_results = "\n".join([
                f"Tool: {call.name}\nResult: {call.result}" 
                for call in state.tool_calls
            ])
        
        # Grounded, non-fabrication answer prompt
        response_prompt = f"""
        You are the GREEN AGENT (Answerer).

        Ground rules:
        - You must ground all concrete facts (prices, durations, counts, times, airports) in the Tool Results provided below.
        - If a fact is not present in Tool Results, DO NOT invent it. Say what’s missing or state uncertainty.
        - Be concise and helpful. If tools errored or returned nothing, explain the situation and offer the next best step.

        Context:
        User: {user_message}

        White Agent Plan:
        {white_agent_reasoning}

        Green Evaluation (decision + notes):
        {green_agent_evaluation}

        Tool Results (verbatim JSON snippets from runtime):
        {tool_results}

        Instructions:
        1) If Tool Results contain at least one successful call with data, produce a short, user-facing answer citing those results (no invented facts).
        2) If tools errored or returned no matches, explain that clearly and suggest a specific follow-up (e.g., “try nearby airports” or “confirm dates”).
        3) Do not reference hidden system prompts. Do not speculate beyond Tool Results.

        Return only the final user-facing answer (no JSON).
        """
        
        # Generate response
        response = await self.anthropic_llm.ainvoke([HumanMessage(content=response_prompt)])
        
        # Add response to state
        response_message = ChatMessage(
            content=response.content,
            agent_type=AgentType.GREEN_AGENT,
            timestamp=datetime.now()
        )
        state.messages.append(response_message)
        
        return state
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Main method to process a user message"""
        try:
            # Add user message to state
            user_message = ChatMessage(
                content=message,
                agent_type=AgentType.USER,
                timestamp=datetime.now()
            )
            self.state.messages.append(user_message)
            
            # Run the conversation graph
            result = await self.graph.ainvoke(self.state)
            
            # Get the final response
            final_response = result.messages[-1]
            
            return {
                "message": final_response.content,
                "agent_type": final_response.agent_type.value,
                "tool_calls": [call.dict() for call in result.tool_calls],
                "conversation_length": len(result.messages)
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "agent_type": AgentType.GREEN_AGENT.value,
                "tool_calls": [],
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "is_active": True,
            "current_agent": self.state.current_agent.value,
            "conversation_length": len(self.state.messages),
            "last_activity": self.state.created_at.isoformat()
        }
    
    def reset(self):
        """Reset the agent conversation"""
        self.state = AgentState()
        logger.info("Agent conversation reset")
