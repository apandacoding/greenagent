"""
FastAPI server for White Agent - AgentBeats compatible.
Runs on a separate port from the green agent.
"""
from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.agent import WhiteAgent
from chatbot.models import ChatMessage, AgentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="White Agent API",
    description="AI reasoning agent for travel planning",
    version="1.0.0"
)

# Configure CORS - same logic as green agent
# Get allowed origins from environment variable or use defaults
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
enable_ngrok = os.getenv("ENABLE_NGROK", "false").lower() == "true"

if allowed_origins_env:
    # Split comma-separated origins from environment variable
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default to localhost for development
    allowed_origins = [
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173"
    ]

# Build CORS configuration
cors_kwargs = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if enable_ngrok:
    # Allow localhost + ngrok domains + cloudflare domains via regex
    cors_kwargs["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1|.*\.ngrok\.io|.*\.ngrok-free\.app|.*\.trycloudflare\.com)(:\d+)?"
else:
    cors_kwargs["allow_origins"] = allowed_origins

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Initialize White Agent
white_agent = WhiteAgent()


def get_agent_card(agent_id: str = None, base_url: str = None):
    """Get White Agent Card metadata in A2A protocol format (0.3.0)"""
    # Construct agent URL if agent_id and base_url are provided
    agent_url = None
    if agent_id and base_url:
        agent_url = f"{base_url.rstrip('/')}/to_agent/{agent_id}"
    
    return {
        "capabilities": {},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "description": "A general-purpose white agent for task fulfillment.",
        "name": "general_white_agent",
        "preferredTransport": "JSONRPC",
        "protocolVersion": "0.3.0",
        "skills": [
            {
                "description": "Handles user requests and completes tasks",
                "examples": [],
                "id": "task_fulfillment",
                "name": "Task Fulfillment",
                "tags": ["general"]
            }
        ],
        "url": agent_url,
        "version": "1.0.0"
    }


@app.get("")
@app.get("/")
async def root():
    """Root endpoint returning White Agent Card metadata for AgentBeats"""
    # For root endpoint, we don't have agent_id yet, so return without URL
    return get_agent_card()


@app.get("/to_agent/{agent_id}")
@app.get("/to_agent/{agent_id}/")
async def to_agent(agent_id: str, request: Request):
    """A2A protocol endpoint - returns Agent Card for specific agent ID"""
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    return get_agent_card(agent_id=agent_id, base_url=base_url)


@app.get("/to_agent/{agent_id}/.well-known/agent-card.json")
async def agent_card_json(agent_id: str, request: Request):
    """A2A protocol endpoint - returns Agent Card JSON"""
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    return get_agent_card(agent_id=agent_id, base_url=base_url)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "agent_type": "white"}


@app.get("/status")
async def get_status():
    """Get current white agent status"""
    return white_agent.get_status()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    agent_type: str
    conversation_length: int
    error: str | None = None


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint for White Agent"""
    try:
        logger.info(f"[WhiteAgent] Received message: {request.message}")
        
        # Process message through WhiteAgent
        result = await white_agent.process_message(request.message)
        
        return ChatResponse(
            message=result.get("message", ""),
            agent_type=result.get("agent_type", "white_agent"),
            conversation_length=result.get("conversation_length", 0),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"[WhiteAgent] Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset():
    """Reset the white agent conversation"""
    white_agent.reset()
    return {"message": "White agent reset successfully"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

