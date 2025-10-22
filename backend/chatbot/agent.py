"""
Green Agent implementation using LangGraph for flight booking chatbot.
"""
import asyncio
import logging
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
        reasoning_prompt = f"""
        You are the White Agent, responsible for reasoning about user requests.
        Analyze the following user message and determine:
        1. What the user is asking for
        2. What tools or actions might be needed
        3. Your reasoning process
        
        User message: {user_message}
        
        Provide your reasoning and any tool calls you think are necessary.
        """
        
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
        
        # Create evaluation prompt
        evaluation_prompt = f"""
        You are the Green Agent, responsible for evaluating the White Agent's reasoning.
        
        White Agent's reasoning: {white_agent_message}
        
        Evaluate:
        1. Is the reasoning sound?
        2. Are the proposed tool calls appropriate?
        3. What improvements or corrections are needed?
        4. Should we proceed with tool calls or generate a response?
        
        Provide your evaluation and decision.
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
        """Determine if tools should be used based on Green Agent's evaluation"""
        # Simple heuristic: if the message contains flight-related keywords, use tools
        user_message = state.messages[0].content.lower()
        flight_keywords = ["flight", "book", "travel", "trip", "airline", "destination"]
        
        if any(keyword in user_message for keyword in flight_keywords):
            return "tools"
        return "response"
    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute necessary tools"""
        logger.info("Executing tools")
        
        user_message = state.messages[0].content
        
        # Determine which tools to use
        tool_calls = []
        
        if "flight" in user_message.lower() or "book" in user_message.lower():
            # Use flight tool
            flight_result = await self.flight_tool.execute(user_message)
            tool_call = ToolCall(
                name="flight_search",
                parameters={"query": user_message},
                result=flight_result,
                status="success"
            )
            tool_calls.append(tool_call)
        
        # Add analysis tool
        analysis_result = await self.analysis_tool.execute(user_message)
        analysis_call = ToolCall(
            name="analysis",
            parameters={"query": user_message},
            result=analysis_result,
            status="success"
        )
        tool_calls.append(analysis_call)
        
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
        
        response_prompt = f"""
        Based on the conversation flow:
        
        User: {user_message}
        White Agent Reasoning: {white_agent_reasoning}
        Green Agent Evaluation: {green_agent_evaluation}
        
        Tool Results:
        {tool_results}
        
        Generate a helpful, accurate response to the user. Be conversational and informative.
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
