"""
Simplified FastAPI server for Green Agent without complex dependencies.
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path to import flights.py
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install fastapi uvicorn")
    sys.exit(1)

# Import flights functionality
try:
    # Change to parent directory to find flights.py and functions/
    import os
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    from flights import flight_tool
    print("✅ Successfully imported flights.py")
except ImportError as e:
    print(f"Warning: Could not import flights.py: {e}")
    flight_tool = None
except Exception as e:
    print(f"Warning: Error with flights.py: {e}")
    flight_tool = None

# Initialize FastAPI app
app = FastAPI(title="Green Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)

manager = ConnectionManager()

class ChatMessage(BaseModel):
    content: str

class ChatResponse(BaseModel):
    message: str
    agent_type: str = "green_agent"
    tool_calls: list = []
    status: str = "success"

@app.get("/")
async def root():
    return {"message": "Green Agent API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "flight_tool_available": flight_tool is not None
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint"""
    try:
        print(f"Received message: {message.content}")
        
        # Simple response logic
        response_message = await process_message(message.content)
        
        return ChatResponse(
            message=response_message,
            agent_type="green_agent",
            tool_calls=[],
            status="success"
        )
    
    except Exception as e:
        print(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_message(message: str) -> str:
    """Process user message and generate response"""
    
    # Check if it's a flight-related query
    flight_keywords = ["flight", "book", "travel", "trip", "airline", "destination", "fly"]
    is_flight_query = any(keyword in message.lower() for keyword in flight_keywords)
    
    if is_flight_query and flight_tool:
        try:
            # Use the flight tool
            flight_data = flight_tool(message)
            
            if flight_data is not None and not flight_data.empty:
                return f"I found {len(flight_data)} flight options for you! Here are the details:\n\n{flight_data.to_string()}"
            else:
                return "I couldn't find any flights matching your criteria. Please try different dates or destinations."
        except Exception as e:
            return f"I encountered an error searching for flights: {str(e)}. Please try again with different search terms."
    else:
        # General response
        return f"Thank you for your message: '{message}'. I'm the Green Agent, and I can help you with flight bookings and travel planning. Please ask me about flights, destinations, or travel planning!"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            print(f"WebSocket message: {message_data}")
            
            # Process message
            response_message = await process_message(message_data["message"])
            
            # Send response back
            response_data = {
                "message": response_message,
                "agent_type": "green_agent",
                "tool_calls": [],
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(
                json.dumps(response_data), 
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    print("Starting Green Agent server...")
    print("Frontend: http://localhost:8002")
    print("Backend API: http://localhost:8000")
    print("WebSocket: ws://localhost:8000/ws")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
