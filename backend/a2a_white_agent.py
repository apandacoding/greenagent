"""White Agent using A2A framework - integrates with existing WhiteAgent for AgentBeats compatibility."""

import uvicorn
import os
import logging
import sys
import uuid
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.agent import WhiteAgent
from chatbot.models import ChatMessage, AgentType

logger = logging.getLogger(__name__)


class WhiteAgentExecutor(AgentExecutor):
    """A2A executor that wraps the existing WhiteAgent."""
    
    def __init__(self):
        # Initialize the existing WhiteAgent
        self.white_agent = WhiteAgent()
        # Track conversations by context_id
        self.ctx_id_to_messages = {}
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute task using the existing WhiteAgent."""
        user_input = context.get_user_input()
        context_id = context.context_id
        
        logger.info(f"[A2A White] Received message (ctx={context_id}): {user_input[:100]}...")
        
        try:
            # Process through existing WhiteAgent
            result = await self.white_agent.process_message(user_input)
            
            # Extract the message from result
            message = result.get("message", "Task completed.")
            
            # Send response via event queue
            await event_queue.enqueue_event(
                new_agent_text_message(message, context_id=context_id)
            )
        except Exception as e:
            logger.error(f"[A2A White] Error: {e}", exc_info=True)
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error processing request: {str(e)}", context_id=context_id)
            )
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution."""
        raise NotImplementedError


def prepare_white_agent_card(url: str = None):
    """Prepare Agent Card for White Agent."""
    skill = AgentSkill(
        id="task_fulfillment",
        name="Task Fulfillment",
        description="Handles user requests and completes tasks",
        tags=["general"],
        examples=[],
    )
    
    card = AgentCard(
        name="general_white_agent",
        description="A general-purpose white agent for task fulfillment.",
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
        preferred_transport="JSONRPC",
        protocol_version="0.3.0",
    )
    return card


def start_white_agent(host: str = "0.0.0.0", port: int = 8002):
    """Start the white agent using A2A framework."""
    logger.info("Starting White Agent with A2A framework...")
    
    # Get agent URL from environment or construct it
    agent_url = os.getenv("AGENT_URL") or os.getenv("CLOUDRUN_HOST")
    if agent_url:
        if not agent_url.startswith("http"):
            agent_url = f"https://{agent_url}"
    else:
        agent_url = f"http://{host}:{port}"
    
    card = prepare_white_agent_card(agent_url)
    card_dict = card.model_dump()
    
    request_handler = DefaultRequestHandler(
        agent_executor=WhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    # Generate a unique agent ID for this instance
    agent_id = str(uuid.uuid4()).replace("-", "")
    
    # Create endpoint handlers
    async def status_endpoint(request):
        return JSONResponse({
            "maintained_agents": 1,
            "running_agents": 1,
            "starting_command": "python a2a_main.py run"
        })
    
    async def agents_endpoint(request):
        """Return agent information - required by AgentBeats controller"""
        agent_instance_url = f"{agent_url.rstrip('/')}/to_agent/{agent_id}"
        return JSONResponse({
            agent_id: {
                "url": agent_instance_url,
                "internal_port": port,
                "state": "running"
            }
        })
    
    # Create agent-specific card with URL including the agent path
    agent_specific_url = f"{agent_url.rstrip('/')}/to_agent/{agent_id}"
    agent_specific_card = prepare_white_agent_card(agent_specific_url)
    agent_specific_card_dict = agent_specific_card.model_dump()
    
    async def root_endpoint(request):
        """Root endpoint - return agent card"""
        return JSONResponse(card_dict)
    
    async def well_known_agent_card(request):
        """/.well-known/agent-card.json endpoint"""
        return JSONResponse(card_dict)
    
    async def to_agent_endpoint(request):
        """A2A protocol endpoint - /to_agent/{agent_id}"""
        # Return agent card with agent-specific URL
        return JSONResponse(agent_specific_card_dict)
    
    async def to_agent_well_known_endpoint(request):
        """A2A protocol endpoint - /to_agent/{agent_id}/.well-known/agent-card.json"""
        # Return agent card with agent-specific URL
        return JSONResponse(agent_specific_card_dict)
    
    async def reset_agent_endpoint(request):
        """Reset endpoint for AgentBeats - POST /agents/{agent_id}/reset"""
        return JSONResponse({"status": "ok", "message": "Agent reset successfully"})
    
    async def agent_status_endpoint(request):
        """Agent status endpoint for AgentBeats - GET /agents/{agent_id}"""
        agent_instance_url = f"{agent_url.rstrip('/')}/to_agent/{agent_id}"
        return JSONResponse({
            "id": agent_id,
            "url": agent_instance_url,
            "internal_port": port,
            "state": "running"
        })
    
    # Build the A2A app to get its routes
    a2a_app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )
    a2a_starlette = a2a_app.build()
    
    # Get A2A routes (for JSON-RPC handling)
    a2a_routes = list(a2a_starlette.routes)
    
    # Create custom routes - these go FIRST to take precedence
    # Note: POST at /to_agent/{agent_id} is handled by A2A routes for JSON-RPC
    custom_routes = [
        Route("/", root_endpoint, methods=["GET", "HEAD"]),
        Route("/status", status_endpoint, methods=["GET"]),
        Route("/agents", agents_endpoint, methods=["GET"]),
        Route("/agents/{agent_id}/reset", reset_agent_endpoint, methods=["POST"]),
        Route("/agents/{agent_id}", agent_status_endpoint, methods=["GET"]),
        Route("/.well-known/agent-card.json", well_known_agent_card, methods=["GET"]),
        Route("/to_agent/{agent_id}", to_agent_endpoint, methods=["GET", "HEAD"]),
        Route("/to_agent/{agent_id}/.well-known/agent-card.json", to_agent_well_known_endpoint, methods=["GET"]),
    ]
    
    # Combine routes: custom first, then A2A routes
    all_routes = custom_routes + a2a_routes
    
    # Create new Starlette app with combined routes
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
    
    app = Starlette(routes=all_routes, middleware=middleware)
    
    logger.info(f"White Agent starting on {host}:{port}")
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"Agent URL: {agent_url}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()
    
    start_white_agent(host=args.host, port=args.port)
