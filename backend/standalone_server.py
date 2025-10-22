"""
Standalone FastAPI server for Green Agent without external dependencies.
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install fastapi uvicorn")
    exit(1)

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
        "mode": "standalone"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint"""
    try:
        print(f"Received message: {message.content}")
        
        # Process message
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
    
    if is_flight_query:
        return f"""🛫 Flight Search Response:

I understand you're looking for flights! Here's what I can help you with:

**Your request:** "{message}"

**Green Agent Analysis:**
✅ Request understood - flight search needed
✅ Analyzing travel requirements
✅ Preparing search parameters

**Mock Flight Results:**
✈️ **Flight Option 1:** New York → Los Angeles
   - Departure: 9:00 AM, Arrival: 12:30 PM
   - Airline: American Airlines
   - Price: $299
   - Duration: 5h 30m

✈️ **Flight Option 2:** New York → Los Angeles  
   - Departure: 2:15 PM, Arrival: 5:45 PM
   - Airline: Delta
   - Price: $325
   - Duration: 5h 30m

**Green Agent Evaluation:**
- Both options are valid and reasonably priced
- Consider your preferred departure time
- Check baggage policies for each airline

Would you like me to help you book one of these flights or search for different dates/destinations?"""
    else:
        return f"""🤖 Green Agent Response:

Thank you for your message: "{message}"

**White Agent Reasoning:**
- User is asking about: {message}
- This appears to be a general inquiry
- No specific tools needed at this time

**Green Agent Evaluation:**
- Reasoning is appropriate for the request
- No flight booking tools required
- Ready to provide general assistance

**My Response:**
I'm the Green Agent, and I'm here to help you with travel planning and flight bookings! 

I can assist you with:
✈️ Flight searches and bookings
🗺️ Travel planning and recommendations  
💰 Price comparisons
📅 Date and destination suggestions

Please let me know if you'd like to search for flights or need help with any travel-related questions!"""

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
    print("🚀 Starting Green Agent standalone server...")
    print("🌐 Frontend: http://localhost:8002")
    print("🔧 Backend API: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("📝 Mode: Standalone (no external dependencies)")
    
    uvicorn.run(
        "standalone_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
