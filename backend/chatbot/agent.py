"""
Green Agent implementation using LangGraph for flight booking chatbot.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
from copy import deepcopy
import anthropic

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from .models import AgentType, ChatMessage, ToolCall
from .config import settings
from langgraph.prebuilt import create_react_agent
from .tools import FlightSearchTool

logger = logging.getLogger(__name__)

# Note: create_react_agent is initialized per-instance in WhiteAgent.__init__
# to ensure proper API key handling


class AgentState(TypedDict, total=False):
    """State for the Green Agent conversation"""
    messages: List[ChatMessage]
    current_agent: str
    tool_calls: List[ToolCall]
    conversation_id: str
    created_at: str
    retry_reasoning: bool
    retry_count: int

class WhiteAgent:
    """White Agent class using LangGraph for conversation flow"""
    def __init__(self):
        self.state: AgentState = {
            "messages": [],
            "current_agent": AgentType.USER.value,
            "tool_calls": [],
            "conversation_id": "",
            "created_at": datetime.now().isoformat(),
            "retry_reasoning": False,
            "retry_count": 0,
        }
        
        # Initialize react agent with proper API key and system prompt
        self.tools = [FlightSearchTool()]
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5",
            api_key=settings.anthropic_api_key
        )
        self.agent = create_react_agent(self.llm, self.tools)
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""
        workflow = StateGraph(AgentState)

        workflow.add_node("user_input", self._process_user_input)
        workflow.add_node("white_agent", self._white_agent_reasoning)
        workflow.add_node("response_generation", self._generate_response)

        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "white_agent")
        workflow.add_edge("white_agent", "response_generation")

        def _route_from_response_generation(state: AgentState):
            # loop if supervisor asked for retry
            return "white_agent" if state.get("retry_reasoning", False) else END

        workflow.add_conditional_edges("response_generation", _route_from_response_generation)
        return workflow.compile()
    
    
    async def _validate_output(self, user_message: str, white_agent_output: str) -> Dict[str, Any]:
        """Validate the output of the White Agent"""
        logger.info("Validating White Agent output")

        system_prompt = f"""
        You are the Supervisor Agent, responsible for reasoning about user requests.
        Analyze the following White Agent output and determine:
        1. If the White Agent's output is valid
        2. If the White Agent's output is faulty

        A faulty output is one that isn't consistent with the user message or the tools or actions might be needed.
        A valid output is one that is consistent with the user message or the tools or actions might be needed.
        
        User message: {user_message}
        White Agent output: {white_agent_output}

        """
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        output_schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["valid", "faulty"],
                    "description": "Whether the output aligns with the user request."
                },
                "reason": {
                    "type": "string",
                    "description": "Explanation of why the output was faulty, required only if status=faulty."
                }
            },
            "required": ["status"],
            "if": {
                "properties": {"status": {"const": "faulty"}}
            },
            "then": {
                "required": ["reason"]
            }
        }

        response = client.messages.create(
            model="claude-sonnet-4-5",
            system=system_prompt,
            messages=[
                {"role": "user", "content": white_agent_output}
            ],
            tools=[
                {
                    "name": "output_validator",
                    "description": "Validates if the White Agent output aligns with the user request using the specified schema.",
                    "input_schema": output_schema
                }
            ],
            tool_choice={"type": "tool", "name": "output_validator"},
            max_tokens=1024,
        )

        return response.content[0].input
    
    async def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Supervisor: validate and decide whether to END or loop."""
        logger.info("Supervisor validation step")

        messages = state.get("messages", [])
        if len(messages) < 2:
            # Not enough context to validate; end.
            return {
                "messages": messages,
                "current_agent": state.get("current_agent", AgentType.USER.value),
                "retry_reasoning": False
            }

        user_msg = messages[-2].content
        white_agent_output = messages[-1].content

        try:
            validation_result = await self._validate_output(user_msg, white_agent_output)
            status = validation_result.get("status", "faulty")

            new_messages = deepcopy(messages)

            if status == "valid":
                supervisor_msg = ChatMessage(
                    content="✅ Output validated: aligns with user intent.",
                    agent_type=AgentType.SUPERVISOR,
                    timestamp=datetime.now()
                )
                new_messages.append(supervisor_msg)
                return {
                    "messages": new_messages,
                    "current_agent": AgentType.SUPERVISOR.value,
                    "retry_reasoning": False
                }

            # faulty → add feedback and loop
            reason = validation_result.get("reason", "Unknown validation failure")
            supervisor_msg = ChatMessage(
                content=f"❌ Faulty output: {reason}\nRetrying reasoning...",
                agent_type=AgentType.SUPERVISOR,
                timestamp=datetime.now()
            )
            new_messages.append(supervisor_msg)

            retry_count = state.get("retry_count", 0) + 1
            if retry_count > 3:
                stop_msg = ChatMessage(
                    content="Supervisor: too many retries; stopping.",
                    agent_type=AgentType.SUPERVISOR,
                    timestamp=datetime.now()
                )
                new_messages.append(stop_msg)
                return {
                    "messages": new_messages,
                    "current_agent": AgentType.SUPERVISOR.value,
                    "retry_reasoning": False,
                    "retry_count": retry_count
                }

            return {
                "messages": new_messages,
                "current_agent": AgentType.SUPERVISOR.value,
                "retry_reasoning": True,      # <-- key: let the graph route back
                "retry_count": retry_count
            }

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            new_messages = deepcopy(messages)
            new_messages.append(ChatMessage(
                content=f"Supervisor error: {e}",
                agent_type=AgentType.SUPERVISOR,
                timestamp=datetime.now()
            ))
            return {
                "messages": new_messages,
                "current_agent": AgentType.SUPERVISOR.value,
                "retry_reasoning": False
            }

    async def _process_user_input(self, state: AgentState) -> Dict[str, Any]:
        """No-op: you already append the user message in process_message()."""
        print("Processing user input")
        print(state)
        return {
            "messages": state.get("messages", []),
            "current_agent": AgentType.USER.value
        }
    
    async def _white_agent_reasoning(self, state: AgentState) -> Dict[str, Any]:
        """White Agent reasoning and analysis"""
        logger.info("White Agent reasoning")
        print("White Agent reasoning")
        messages = state.get("messages", [])
        if not messages:
            # nothing to reason about; just pass through
            return {"messages": messages, "current_agent": AgentType.WHITE_AGENT.value}

        # Build conversation history for the react agent
        # Convert our ChatMessage objects to LangChain message format
        langchain_messages = []
        conversation_context = []  # For tool context injection
        
        for msg in messages:
            if msg.agent_type == AgentType.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
                conversation_context.append({"role": "user", "content": msg.content})
            elif msg.agent_type == AgentType.WHITE_AGENT:
                langchain_messages.append(AIMessage(content=msg.content))
                conversation_context.append({"role": "assistant", "content": msg.content})
            elif msg.agent_type == AgentType.TOOL:
                # Include tool messages in conversation context
                conversation_context.append({"role": "tool", "content": msg.content})
        
        # Inject conversation context into FlightSearchTool
        for tool in self.tools:
            if isinstance(tool, FlightSearchTool):
                tool.set_context(conversation_context)
        
        print(f"Sending {len(langchain_messages)} messages to react agent")
        print(f"Tool context: {len(conversation_context)} messages")
        print(f"Last message: {langchain_messages[-1].content if langchain_messages else 'None'}")

        # Invoke the react agent with FULL conversation history
        response = await self.agent.ainvoke({"messages": langchain_messages})
        print(f"React agent returned {len(response.get('messages', []))} messages")

        new_messages = deepcopy(messages)
        
        # Convert LangChain messages to ChatMessage objects
        # Only add NEW messages (skip the ones we sent)
        existing_count = len(langchain_messages)
        for msg in response.get("messages", [])[existing_count:]:
            # Determine agent type based on message type
            if isinstance(msg, AIMessage):
                agent_type = AgentType.WHITE_AGENT
            elif isinstance(msg, ToolMessage):
                # DON'T skip ToolMessages - capture them!
                agent_type = AgentType.TOOL
            else:
                agent_type = AgentType.WHITE_AGENT
            
            chat_msg = ChatMessage(
                content=str(msg.content),
                agent_type=agent_type,
                timestamp=datetime.now()
            )
            new_messages.append(chat_msg)
            print(f"Added message: {agent_type.value} - {str(msg.content)[:100]}...", flush=True)

        return {
            "messages": new_messages,
            "current_agent": AgentType.WHITE_AGENT.value,
            "retry_reasoning": False
        }
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Main method to process a user message"""
        try:
            # append user message ONCE here
            self.state["messages"].append(ChatMessage(
                content=message,
                agent_type=AgentType.USER,
                timestamp=datetime.now()
            ))

            result = await self.graph.ainvoke(self.state)
            
            # IMPORTANT: Update self.state with the result to persist conversation history
            self.state = result

            msgs = result.get("messages", [])
            
            # Find the last WHITE_AGENT or TOOL message (skip supervisor validation messages)
            white_agent_response = None
            for msg in reversed(msgs):
                if msg.agent_type in (AgentType.WHITE_AGENT, AgentType.TOOL):
                    white_agent_response = msg
                    break
            
            if white_agent_response:
                return {
                    "message": white_agent_response.content,
                    "agent_type": white_agent_response.agent_type.value,
                    "conversation_length": len(msgs),
                    "conversation_history": len(msgs)  # Show full history count
                }
            
            # Fallback to last message if no white agent message found
            final = msgs[-1] if msgs else None
            if final:
                return {
                    "message": final.content,
                    "agent_type": final.agent_type.value,
                    "conversation_length": len(msgs)
                }
            return {
                "message": "No response generated",
                "agent_type": AgentType.USER.value,
                "conversation_length": 0
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "agent_type": AgentType.USER.value,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "is_active": True,
            "current_agent": self.state.get("current_agent", AgentType.USER.value),
            "conversation_length": len(self.state.get("messages", [])),
            "last_activity": self.state.get("created_at", datetime.now().isoformat())
        }
    
    def reset(self):
        """Reset the agent conversation"""
        self.state = {
            "messages": [],
            "current_agent": AgentType.USER.value,
            "tool_calls": [],
            "conversation_id": "",
            "created_at": datetime.now().isoformat(),
            "retry_reasoning": False,
            "retry_count": 0,
        }
        logger.info("Agent conversation reset")


class GreenAgent:
    """Main Green Agent class using LangGraph for conversation flow"""
    
    def __init__(self):
        self.state: AgentState = {
            "messages": [],
            "current_agent": AgentType.USER.value,
            "tool_calls": [],
            "conversation_id": "",
            "created_at": datetime.now().isoformat()
        }
        self.flight_tool = FlightSearchTool()
        
        # Initialize LLMs
        self.anthropic_llm = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.7
        )
        
        # OpenAI is optional - only initialize if API key is set
        try:
            if settings.openai_api_key:
                self.openai_llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0.7
                )
            else:
                self.openai_llm = None
                logger.warning("OpenAI API key not set - using Anthropic LLM only")
        except Exception as e:
            self.openai_llm = None
            logger.warning(f"Failed to initialize OpenAI LLM: {e}")
        
        # Build the conversation graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("user_input", self._process_user_input)
        workflow.add_node("white_agent", self._white_agent_reasoning)
        workflow.add_node("green_agent", self._green_agent_evaluation)
        workflow.add_node("response_generation", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "white_agent")
        workflow.add_edge("white_agent", "green_agent")
        workflow.add_edge("green_agent", "response_generation")
        workflow.add_edge("response_generation", END)
        
        return workflow.compile()
    
    async def _process_user_input(self, state: AgentState) -> Dict[str, Any]:
        """No-op: you already append the user message in process_message()."""
        return {
            "messages": state.get("messages", []),
            "current_agent": AgentType.USER.value
        }
    
    async def _white_agent_reasoning(self, state: AgentState) -> Dict[str, Any]:
        """White Agent reasoning and analysis"""
        logger.info("White Agent reasoning")
        
        # Get the latest user message
        messages = state.get("messages", [])
        user_message = messages[-1].content
        
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
        messages = messages.copy()
        messages.append(reasoning_message)
        
        return {"messages": messages, "current_agent": AgentType.WHITE_AGENT.value}
    
    async def _green_agent_evaluation(self, state: AgentState) -> Dict[str, Any]:
        """Green Agent evaluation of White Agent's reasoning"""
        logger.info("Green Agent evaluation")
        
        # Get White Agent's reasoning
        messages = state.get("messages", [])
        white_agent_message = messages[-1].content
        
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
        messages = messages.copy()
        messages.append(evaluation_message)
        
        return {"messages": messages, "current_agent": AgentType.GREEN_AGENT.value}
    
    
    async def _execute_tools(self, state: AgentState) -> Dict[str, Any]:
        """Execute necessary tools"""
        logger.info("Executing tools")
        
        messages = state.get("messages", [])
        user_message = messages[0].content
        
        # Determine which tools to use
        tool_calls = []
        
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
        
        return {"tool_calls": tool_calls, "messages": messages}
    
    async def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate final response"""
        logger.info("Generating response")
        
        # Combine all information for response generation
        messages = state.get("messages", [])
        user_message = messages[0].content
        white_agent_reasoning = messages[1].content
        green_agent_evaluation = messages[2].content
        
        # Include tool results if available
        tool_results = ""
        tool_calls = state.get("tool_calls", [])
        if tool_calls:
            tool_results = "\n".join([
                f"Tool: {call.name}\nResult: {call.result}" 
                for call in tool_calls
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
        messages = messages.copy()
        messages.append(response_message)
        
        return {"messages": messages, "current_agent": AgentType.GREEN_AGENT.value, "tool_calls": tool_calls}
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Main method to process a user message"""
        try:
            # Add user message to state
            user_message = ChatMessage(
                content=message,
                agent_type=AgentType.USER,
                timestamp=datetime.now()
            )
            self.state["messages"].append(user_message)
            
            # Run the conversation graph
            result = await self.graph.ainvoke(self.state)
            
            # Get the final response
            messages = result.get("messages", [])
            final_response = messages[-1]
            tool_calls = result.get("tool_calls", [])
            
            return {
                "message": final_response.content,
                "agent_type": final_response.agent_type.value,
                "tool_calls": [call.dict() for call in tool_calls] if tool_calls else [],
                "conversation_length": len(messages)
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
            "current_agent": self.state.get("current_agent", AgentType.USER.value),
            "conversation_length": len(self.state.get("messages", [])),
            "last_activity": self.state.get("created_at", datetime.now().isoformat())
        }
    
    def reset(self):
        """Reset the agent conversation"""
        self.state = {
            "messages": [],
            "current_agent": AgentType.USER.value,
            "tool_calls": [],
            "conversation_id": "",
            "created_at": datetime.now().isoformat()
        }
        logger.info("Agent conversation reset")
