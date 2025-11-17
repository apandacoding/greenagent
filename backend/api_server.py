"""
FastAPI server for Green Agent chatbot with CORS support.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.agent import WhiteAgent, GreenAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Green Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
white_agent = WhiteAgent()
green_agent = GreenAgent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    agent_type: str
    conversation_length: int
    error: str | None = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Green Agent API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_white_agent(request: ChatRequest):
    """
    Chat endpoint for White Agent (reasoning engine)
    """
    try:
        logger.info(f"Received message: {request.message}")
        
        # Process message through WhiteAgent
        result = await white_agent.process_message(request.message)
        
        return ChatResponse(
            message=result.get("message", ""),
            agent_type=result.get("agent_type", "white_agent"),
            conversation_length=result.get("conversation_length", 0),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/green", response_model=ChatResponse)
async def chat_green_agent(request: ChatRequest):
    """
    Chat endpoint for Green Agent (full demo)
    """
    try:
        logger.info(f"Received message for Green Agent: {request.message}")
        
        # Process message through GreenAgent
        result = await green_agent.process_message(request.message)
        
        return ChatResponse(
            message=result.get("message", ""),
            agent_type=result.get("agent_type", "green_agent"),
            conversation_length=result.get("conversation_length", 0),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """Get current agent status"""
    return {
        "white_agent": white_agent.get_status(),
        "green_agent": green_agent.get_status()
    }


@app.post("/api/reset")
async def reset_agents():
    """Reset all agents"""
    white_agent.reset()
    green_agent.reset()
    return {"message": "Agents reset successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

