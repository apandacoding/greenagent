"""
Green Agent implementation using LangGraph for flight booking / travel chatbot.
- Deterministic planner/validator prompts
- Dynamic tool registry (flight/hotel/etc.) discovered from .tools
- Tiny JSONL ledger for traces
- NDCG@K evaluator entrypoint
"""
from __future__ import annotations

import asyncio
import inspect
import importlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI  # reserved (not used here)

from .models import AgentType, ChatMessage, ToolCall
from .tools import FlightTool, AnalysisTool
from .config import settings
from .ledger import Ledger
from .metrics import ndcg_at_k

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

        # Built-in tools this agent already used
        self.flight_tool = FlightTool()
        self.analysis_tool = AnalysisTool()

        # Initialize LLMs (keep deterministic for planning/validation)
        self.anthropic_llm = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.0,
        )
        self.openai_llm = ChatOpenAI(  # reserved for future use
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.0,
        )

        # Tiny JSONL ledger (writes to runs/<run_id>/trace.jsonl)
        self.ledger = Ledger(settings)

        # Dynamic tool registry (adds hotel/weather/etc. if present in .tools)
        self.tool_registry = self._build_tool_registry()

        # Build the conversation graph
        self.graph = self._build_graph()

    # ---------------------------
    # Helpers
    # ---------------------------
    @staticmethod
    def _extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract the first balanced JSON object from text.
        More robust than a greedy regex; ignores prose/code fences around it.
        """
        if not text:
            return None
        start = text.find("{")
        while start != -1:
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except Exception:
                            break  # try next '{'
            start = text.find("{", start + 1)
        return None

    @staticmethod
    def _json_dumps(obj: Any) -> str:
        try:
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return str(obj)

    @staticmethod
    def _latest_message_of_type(state: AgentState, agent_type: AgentType) -> Optional[ChatMessage]:
        for msg in reversed(state.messages):
            if msg.agent_type == agent_type:
                return msg
        return None

    def _build_tool_registry(self) -> Dict[str, Any]:
        """
        Dynamically build a tool registry from available classes in .tools.
        Keys are the *tool names* the White Agent will emit in its JSON plan.
        Values are instantiated tool objects with an async .execute(...) method
        (or sync, which we detect and await if coroutine).
        """
        registry: Dict[str, Any] = {}

        # Always include these
        registry["flight_search"] = self.flight_tool
        registry["analysis"] = self.analysis_tool

        # Load optional tool classes if present (minimally invasive)
        # Prefer relative import; if anything goes wrong, just skip.
        tools_mod = None
        try:
            # `__package__` is this module's package (e.g., backend.chatbot)
            tools_mod = importlib.import_module(f"{__package__}.tools")
        except Exception:
            # Fallback: try relative import directly
            try:
                from . import tools as tools_mod  # type: ignore
            except Exception:
                tools_mod = None

        candidates = {
            "hotel_search": "HotelTool",
            "restaurant_search": "RestaurantTool",
            "car_rental": "CarRentalTool",
            "weather": "WeatherTool",
            "visa": "VisaTool",
            "maps": "MapsTool",
            "currency": "CurrencyTool",
            "calendar": "CalendarTool",
            "activities": "ActivitiesTool",
            "packing_checklist": "PackingChecklistTool",
        }

        if tools_mod:
            for tool_key, cls_name in candidates.items():
                if tool_key in registry:
                    continue
                if hasattr(tools_mod, cls_name):
                    try:
                        cls = getattr(tools_mod, cls_name)
                        registry[tool_key] = cls()
                    except Exception:
                        # Fail open: skip if cannot construct
                        pass

        return registry

    async def _call_tool(self, tool_obj: Any, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Robustly call tool.execute(...). Supports both string 'query' and dict args,
        and both async and sync execute implementations.
        """
        if not hasattr(tool_obj, "execute"):
            return {"status": "error", "message": "Tool missing execute()"}

        try:
            sig = inspect.signature(tool_obj.execute)
            params = [p for p in sig.parameters.values() if p.name != "self"]

            async def _maybe_await(result: Any) -> Any:
                if inspect.isawaitable(result):
                    return await result
                return result

            if len(params) == 0:
                # execute(self)
                return await _maybe_await(tool_obj.execute())
            elif len(params) == 1:
                p = params[0]
                # VAR_POSITIONAL/VAR_KEYWORD → pass dict as kwargs
                if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    return await _maybe_await(tool_obj.execute(**args))
                # Single normal param: prefer 'query' else pass dict
                if "query" in args:
                    return await _maybe_await(tool_obj.execute(args["query"]))
                return await _maybe_await(tool_obj.execute(args))
            else:
                # Multi-params: best effort kwargs
                return await _maybe_await(tool_obj.execute(**args))
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ---------------------------
    # Graph
    # ---------------------------
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""
        workflow = StateGraph(AgentState)

        # Nodes
        workflow.add_node("user_input", self._process_user_input)
        workflow.add_node("white_agent", self._white_agent_reasoning)
        workflow.add_node("green_agent", self._green_agent_evaluation)
        workflow.add_node("tool_execution", self._execute_tools)
        workflow.add_node("response_generation", self._generate_response)

        # Edges
        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "white_agent")
        workflow.add_edge("white_agent", "green_agent")
        workflow.add_conditional_edges(
            "green_agent",
            self._should_use_tools,
            {
                "tools": "tool_execution",
                "response": "response_generation",
            },
        )
        workflow.add_edge("tool_execution", "response_generation")
        workflow.add_edge("response_generation", END)

        return workflow.compile()

    # ---------------------------
    # Nodes
    # ---------------------------
    async def _process_user_input(self, state: AgentState) -> AgentState:
        """
        NO-OP: user message is appended by process_message().
        This node exists to leave room for future pre-processing.
        """
        logger.info("Processing user input (noop)")
        return state

    async def _white_agent_reasoning(self, state: AgentState) -> AgentState:
        """White Agent reasoning and analysis (JSON tool plan only)"""
        logger.info("White Agent reasoning")

        # Get latest user message
        user_msg = self._latest_message_of_type(state, AgentType.USER)
        user_message = user_msg.content if user_msg else ""

        # Build allowed-tools section from the live registry
        tool_names = sorted(self.tool_registry.keys())
        examples = {
            "flight_search":  'args: {"query": "Cheapest nonstop ORD->CUN 2026-07-15 to 2026-07-22, 2 adults, economy"}',
            "hotel_search":   'args: {"query": "All-inclusive family resort in Cancun 2026-07-15..22, kids club, <$500/night"}',
            "restaurant_search": 'args: {"query": "Kid-friendly seafood near hotel, dinner 2026-07-18 18:30, party=4"}',
            "car_rental":     'args: {"query": "Pickup CUN 2026-07-15 12:30, drop 2026-07-22 09:00, SUV, driver_age=38"}',
            "weather":        'args: {"query": "Weather Cancun 2026-07-15..22 with historical averages"}',
            "visa":           'args: {"query": "Visa US->MX tourism 7 days depart 2026-07-15"}',
            "maps":           'args: {"query": "Driving CUN Airport -> Moon Palace, time + steps"}',
            "currency":       'args: {"query": "USD->MXN rate and best practice for cash/cards"}',
            "calendar":       'args: {"query": "Holidays/events in Mexico 2026-07-15..22 relevant to tourists"}',
            "activities":     'args: {"query": "Family snorkeling options near resort, half-day"}',
            "packing_checklist": 'args: {"query": "Packing checklist for family beach week, Cancun"}',
            "analysis":       'args: {"query": "Among current options, choose best value under budget"}',
        }
        allowed_tools_lines = []
        for t in tool_names:
            ex = examples.get(t, 'args: {"query": "<concise instruction>"}')
            allowed_tools_lines.append(f'- "{t}": {ex}')
        allowed_tools_section = "\n".join(allowed_tools_lines)

        reasoning_prompt = (
            """
            You are the WHITE AGENT (Planner).
            Your *only* job is to translate the user's request into a deterministic TOOL PLAN for the GREEN AGENT to validate and execute.
            Do NOT answer the user. Do NOT include any prose outside of JSON. Output exactly one JSON object that follows the schema below.

            ## Allowed tools (only call from this list)
            """
            + allowed_tools_section
            + """
            
            ## Output schema (respond with JSON only)
            {
              "tool_plan_id": "<short id you generate>",
              "rationale": "<1–2 short sentences explaining why these tools are needed>",
              "tool_calls": [
                { "id": "tc1", "tool": "<one of the allowed tools>", "args": { "query": "<string>" } }
                // Additional calls allowed; keep arguments minimal and concrete.
              ]
            }

            ## Rules
            - If NO tool is necessary, set "tool_calls": [] and keep a brief "rationale".
            - Prefer explicit dates like "2026-07-15". If unknown, keep the user's wording in "query".
            - Only use the allowed tools above. Do NOT invent tools or args.
            - Do NOT include markdown fences or any text outside the single JSON object.
            """
            + f"\nUser message: {user_message}\n"
            + "Now, generate ONLY the JSON object for this user's message."
        )

        response = await self.anthropic_llm.ainvoke([HumanMessage(content=reasoning_prompt)])

        # Persist plan to ledger
        self.ledger.log_plan(
            stage="white_agent_plan",
            content=response.content,
            meta={"type": "white_agent", "timestamp": datetime.now().isoformat()},
        )

        # Add to state
        reasoning_message = ChatMessage(
            content=response.content,
            agent_type=AgentType.WHITE_AGENT,
            timestamp=datetime.now(),
        )
        state.messages.append(reasoning_message)

        return state

    def _get_latest_white_plan(self, state: AgentState) -> Optional[Dict[str, Any]]:
        white_msg = self._latest_message_of_type(state, AgentType.WHITE_AGENT)
        if not white_msg:
            return None
        plan = self._extract_first_json_object(white_msg.content)
        if plan and isinstance(plan, dict):
            return plan
        return None

    async def _green_agent_evaluation(self, state: AgentState) -> AgentState:
        """Green Agent validation of White Agent's plan (JSON-only decision)"""
        logger.info("Green Agent evaluation")

        white_msg = self._latest_message_of_type(state, AgentType.WHITE_AGENT)
        white_agent_message = white_msg.content if white_msg else ""

        evaluation_prompt = f"""
        You are the GREEN AGENT (Validator/Executor).

        Your responsibilities:
        1) Parse the WHITE AGENT’s JSON tool plan from the message above.
        2) Validate it against our rules (schema, allowed tools, safe args).
        3) Decide whether to execute tools. Never fabricate tool outputs or “assume” results.

        ## Allowed tools and args
        - flight_search: {{ "query": "<string>" }}
        - analysis:      {{ "query": "<string>" }}
        - plus any others listed in the WHITE plan that match the allowed tools you see there.

        ## Validation rules
        - The plan must be a single JSON object with:
          - tool_plan_id: string
          - rationale: string (1–2 short sentences)
          - tool_calls: array of 0+ calls; each call has {{ id, tool, args }}
        - tool must be one of the allowed tools listed in the WHITE plan prompt (reject unknowns).
        - args must exist and must be a JSON object.
        - For our current tool interfaces, the only required arg is "query" (non-empty string).
        - SAFE NORMALIZATIONS only:
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

        response = await self.anthropic_llm.ainvoke([HumanMessage(content=evaluation_prompt)])

        # Persist eval to ledger
        self.ledger.log_eval(
            stage="green_agent_validation",
            content=response.content,
            meta={"type": "green_agent", "timestamp": datetime.now().isoformat()},
        )

        evaluation_message = ChatMessage(
            content=response.content,
            agent_type=AgentType.GREEN_AGENT,
            timestamp=datetime.now(),
        )
        state.messages.append(evaluation_message)

        return state

    def _get_latest_green_eval(self, state: AgentState) -> Optional[Dict[str, Any]]:
        for msg in reversed(state.messages):
            if msg.agent_type == AgentType.GREEN_AGENT:
                decision = self._extract_first_json_object(msg.content)
                if decision and isinstance(decision, dict) and "decision" in decision:
                    return decision
        return None

    def _should_use_tools(self, state: AgentState) -> str:
        """Use the Green evaluation (fallback to White plan)."""
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
            state.tool_calls = []
            return state

        normalized = eval_json.get("normalized_plan")
        plan = normalized if isinstance(normalized, dict) else (self._get_latest_white_plan(state) or {"tool_calls": []})
        tool_calls: List[ToolCall] = []

        for call in plan.get("tool_calls", []):
            tool_name = call.get("tool")
            args = call.get("args", {}) or {}
            status = "success"

            tool_obj = self.tool_registry.get(tool_name)
            if not tool_obj:
                result = {"status": "error", "message": f"Unknown tool '{tool_name}'"}
            else:
                result = await self._call_tool(tool_obj, args)

            tool_calls.append(
                ToolCall(
                    name=tool_name or "unknown",
                    parameters=args if isinstance(args, dict) else {"query": str(args)},
                    result=result,
                    status=result.get("status", status),
                )
            )

            # Ledger for each tool call
            self.ledger.log_tool_call(
                tool=tool_name or "unknown",
                args=args,
                result=result,
                status=result.get("status", status),
                meta={"timestamp": datetime.now().isoformat()},
            )

        state.tool_calls = tool_calls
        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response grounded ONLY in tool results"""
        logger.info("Generating response")

        user_msg = self._latest_message_of_type(state, AgentType.USER)
        white_msg = self._latest_message_of_type(state, AgentType.WHITE_AGENT)
        green_eval_msg = self._latest_message_of_type(state, AgentType.GREEN_AGENT)

        user_message = user_msg.content if user_msg else ""
        white_agent_reasoning = white_msg.content if white_msg else ""
        green_agent_evaluation = green_eval_msg.content if green_eval_msg else ""

        # Include tool results if available
        tool_results = ""
        if state.tool_calls:
            chunks = []
            for call in state.tool_calls:
                chunks.append(f"Tool: {call.name}\nResult:\n{self._json_dumps(call.result)}")
            tool_results = "\n\n".join(chunks)

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

        Tool Results (verbatim JSON from runtime):
        {tool_results}

        Instructions:
        1) If Tool Results contain at least one successful call with data, produce a short, user-facing answer citing those results (no invented facts).
        2) If tools errored or returned no matches, explain that clearly and suggest a specific follow-up (e.g., “try nearby airports” or “confirm dates”).
        3) Do not reference hidden system prompts. Do not speculate beyond Tool Results.

        Return only the final user-facing answer (no JSON).
        """

        response = await self.anthropic_llm.ainvoke([HumanMessage(content=response_prompt)])

        # Ledger final answer
        self.ledger.log_message(
            role="green_answer",
            content=response.content,
            meta={"timestamp": datetime.now().isoformat()},
        )

        response_message = ChatMessage(
            content=response.content,
            agent_type=AgentType.GREEN_AGENT,
            timestamp=datetime.now(),
        )
        state.messages.append(response_message)

        return state

    # ---------------------------
    # Public API
    # ---------------------------
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Main method to process a user message"""
        try:
            # Append user message once (user_input node is a NO-OP)
            user_message = ChatMessage(
                content=message,
                agent_type=AgentType.USER,
                timestamp=datetime.now(),
            )
            self.state.messages.append(user_message)

            # Ledger user message
            self.ledger.log_message(
                role="user",
                content=message,
                meta={"timestamp": datetime.now().isoformat()},
            )

            # Run the graph
            result: AgentState = await self.graph.ainvoke(self.state)

            # Final response = last GREEN message if present
            final_msg = None
            for msg in reversed(result.messages):
                if msg.agent_type == AgentType.GREEN_AGENT:
                    final_msg = msg
                    break
            final_response = final_msg or result.messages[-1]

            return {
                "message": final_response.content,
                "agent_type": final_response.agent_type.value,
                "tool_calls": [call.dict() for call in result.tool_calls],
                "conversation_length": len(result.messages),
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.ledger.log_error("process_message", str(e))
            return {
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "agent_type": AgentType.GREEN_AGENT.value,
                "tool_calls": [],
                "error": str(e),
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "is_active": True,
            "current_agent": self.state.current_agent.value,
            "conversation_length": len(self.state.messages),
            "last_activity": self.state.created_at.isoformat(),
        }

    def reset(self):
        """Reset the agent conversation"""
        self.state = AgentState()
        logger.info("Agent conversation reset")

    # ---------------------------
    # NDCG entrypoint (for ranked lists like hotels)
    # ---------------------------
    def evaluate_rankings(self, predicted: List[str], ideal: List[str], k: Optional[int] = None) -> Dict[str, Any]:
        """
        Compute NDCG@K for a simple ranked list evaluation.
        - predicted: list of ids (highest rank first)
        - ideal:     list of ids in the ideal order (highest rank first)
        Returns a dict and logs it to the ledger.
        """
        if k is None:
            k = getattr(settings, "ndcg_k", 5)

        # Binary gains by presence in ideal (simple + robust)
        rel = [1 if item in ideal else 0 for item in predicted[:k]]
        score = float(ndcg_at_k(rel, k=k))
        payload = {"k": k, "predicted": predicted[:k], "ideal": ideal[:k], "ndcg": score}

        self.ledger.log(kind="ndcg_eval", payload=payload, meta={"timestamp": datetime.now().isoformat()})
        return payload
