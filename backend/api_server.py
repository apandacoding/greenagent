"""
FastAPI server for Green Agent chatbot with CORS support.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.agent import WhiteAgent, GreenAgent
from green_agent.infrastructure.controller import GreenAgentController
from green_agent.execution.trace_ledger import TraceLedgerManager
from green_agent.streaming.event_queue import get_event_queue
from green_agent.streaming.event_stream import get_event_stream
from green_agent.integration import wrap_white_agent_tools

# Configure logging
# Setup log file capturing
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend.log")

# Ensure root logger writes to file as well
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(console_handler)

# Add file handler
file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

class TeeLogger:
    """Writes to both original stream and a file."""
    def __init__(self, original_stream, filename):
        self.original_stream = original_stream
        self.file = open(filename, 'a', buffering=1, encoding='utf-8')

    def write(self, message):
        try:
            self.original_stream.write(message)
            self.original_stream.flush()  # Force flush to terminal
        except Exception:
            pass
            
        try:
            self.file.write(message)
            self.file.flush()  # Force flush to file
            os.fsync(self.file.fileno())
        except Exception:
            pass

    def flush(self):
        try:
            self.original_stream.flush()
            self.file.flush()
            os.fsync(self.file.fileno())
        except Exception:
            pass

    def close(self):
        self.file.close()

# Redirect stdout and stderr to capture prints (like from tools)
# Check if already redirected to avoid nesting on reloads
if not hasattr(sys.stdout, 'file') or sys.stdout.file.name != LOG_FILE_PATH:
    sys.stdout = TeeLogger(sys.stdout, LOG_FILE_PATH)
    sys.stderr = TeeLogger(sys.stderr, LOG_FILE_PATH)
    logger.info(f"Logging (stdout/stderr) redirected to {LOG_FILE_PATH}")

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
# Green Agent uses the same WhiteAgent instance to avoid duplicate state
green_agent = GreenAgent(white_agent=white_agent)

# Initialize Green Agent controller for fixtures
# Initialize immediately so tools are wrapped at startup
green_controller = GreenAgentController(seed=42, scenario_id="default")
green_controller.start_run()

trace_ledger_manager = TraceLedgerManager(green_controller)
trace_ledger_manager.initialize()

# Initialize event queue to start processing events
event_queue = get_event_queue()

# Wrap White Agent tools to use fixtures - pass event_queue for intermediate step emission
wrap_white_agent_tools(white_agent, green_controller, use_fixtures=True, trace_ledger=trace_ledger_manager, event_queue=event_queue)

def get_green_controller():
    """Get Green Agent controller and trace ledger."""
    return green_controller, trace_ledger_manager

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.event_stream = get_event_stream()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

manager = ConnectionManager()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    agent_type: str
    conversation_length: int
    error: str | None = None
    evaluation_result: dict | None = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Green Agent API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/debug/tools")
async def debug_tools():
    """Debug endpoint to check if tools are wrapped."""
    return {
        "white_agent_has_tools": hasattr(white_agent, 'tools'),
        "num_tools": len(white_agent.tools) if hasattr(white_agent, 'tools') else 0,
        "tools": [tool.name for tool in white_agent.tools] if hasattr(white_agent, 'tools') else [],
        "has_interceptor": hasattr(white_agent, '_tool_interceptor'),
        "has_controller": hasattr(white_agent, '_green_controller'),
        "has_trace_ledger": hasattr(white_agent, '_trace_ledger'),
        "green_controller_active": green_controller is not None,
        "trace_ledger_active": trace_ledger_manager is not None,
    }


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


@app.post("/api/chat/green")
async def chat_green_agent(request: ChatRequest):
    """
    Chat endpoint for Green Agent (evaluates White Agent outputs)
    """
    try:
        logger.info(f"Received message for Green Agent: {request.message}")
        
        # Process message through GreenAgent
        result = await green_agent.process_message(request.message)
        
        # Build response with optional evaluation result
        response_data = {
            "message": result.get("message", ""),
            "agent_type": result.get("agent_type", "green_agent"),
            "conversation_length": result.get("conversation_length", 0),
            "error": result.get("error")
        }
        
        # Include evaluation result if available
        if "evaluation_result" in result:
            response_data["evaluation_result"] = result["evaluation_result"]
        
        return response_data
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


@app.websocket("/ws/green")
async def websocket_green_agent(websocket: WebSocket):
    """
    WebSocket endpoint for Green Agent with real-time tool call and fixture streaming.
    """
    logger.info("[WebSocket] New WebSocket connection attempt")
    
    # Accept connection FIRST - must be done before any other operations
    await websocket.accept()
    logger.info("[WebSocket] Connection accepted successfully")
    
    try:
        controller, ledger = get_green_controller()
        logger.info("[WebSocket] Controller and ledger retrieved")
        
        # Reset trace ledger for new conversation
        run_id = controller.start_run()
        ledger.clear()
        ledger.initialize(run_id)
        logger.info(f"[WebSocket] Trace ledger initialized with run_id: {run_id}")
        
        # Subscribe to event queue for this connection
        event_queue = get_event_queue()
        logger.info("[WebSocket] Event queue retrieved")
        
        # Track if final_response has been sent to avoid streaming late events
        final_response_sent = False

        async def send_event(event: Dict[str, Any]):
            nonlocal final_response_sent
            try:
                # Drop any tool/trace events after final response was sent
                if final_response_sent and event.get("type") in {"tool_call", "tool_call_step", "trace_update", "react_step"}:
                    logger.debug(f"[WebSocket] Skipping event after final response: {event.get('type')}")
                    return

                # Check if websocket is still connected
                try:
                    current_state = websocket.client_state.name if hasattr(websocket.client_state, 'name') else str(websocket.client_state)
                    if current_state != "CONNECTED":
                        logger.debug(f"[WebSocket] Cannot send event, websocket not connected: {current_state}")
                        # Unsubscribe this callback since connection is closed
                        event_queue.unsubscribe(send_event)
                        return
                except Exception:
                    # If we can't check state, try to send anyway
                    pass
                
                logger.info(f"[WebSocket] Sending event to client: {event.get('type', 'unknown')}")
                await websocket.send_json(event)
                logger.info(f"[WebSocket] Event sent successfully: {event.get('type', 'unknown')}")
            except (WebSocketDisconnect, ConnectionError) as e:
                # Client disconnected - this is normal, don't log as error
                logger.debug(f"[WebSocket] Client disconnected while sending event: {event.get('type', 'unknown')}")
                # Unsubscribe this callback since connection is closed
                event_queue.unsubscribe(send_event)
                return
            except RuntimeError as e:
                # Check if it's the "close message" error
                error_str = str(e)
                if "close message" in error_str.lower() or "not connected" in error_str.lower():
                    logger.debug(f"[WebSocket] Connection closed (RuntimeError): {error_str}")
                    # Unsubscribe this callback since connection is closed
                    event_queue.unsubscribe(send_event)
                    return
                else:
                    # Re-raise unexpected RuntimeErrors
                    raise
            except Exception as e:
                # Only log unexpected errors
                error_str = str(e)
                if any(keyword in error_str.lower() for keyword in ["disconnect", "connection closed", "closed", "1006", "1012", "close message"]):
                    logger.debug(f"[WebSocket] Connection closed: {error_str}")
                    # Unsubscribe this callback since connection is closed
                    event_queue.unsubscribe(send_event)
                else:
                    logger.error(f"[WebSocket] Unexpected error sending event: {e}", exc_info=True)
        
        logger.info("[WebSocket] Subscribing to event queue")
        event_queue.subscribe(send_event)
        logger.info("[WebSocket] Event queue subscribed")
        
        # Register with connection manager
        manager.active_connections.append(websocket)
        logger.info(f"[WebSocket] Connection registered. Total: {len(manager.active_connections)}")
    
        # Send initial connection message
        try:
            await websocket.send_json({
                "type": "status",
                "data": {"status": "connected", "message": "WebSocket connected successfully"}
            })
            logger.info("[WebSocket] Initial connection message sent")
        except Exception as e:
            logger.error(f"[WebSocket] Failed to send initial message: {e}", exc_info=True)
            # If we can't send initial message, connection might be broken
            return
        
        # Main message receiving loop
        while True:
            # Receive message from client
            logger.info("[WebSocket] Waiting for message from client...")
            
            try:
                # Check if WebSocket is still connected before receiving
                current_state = websocket.client_state.name if hasattr(websocket.client_state, 'name') else str(websocket.client_state)
                if current_state != "CONNECTED":
                    logger.warning(f"[WebSocket] WebSocket not connected, state: {current_state}")
                    logger.warning(f"[WebSocket] WebSocket accept was called, but state is: {current_state}")
                    # Try to verify accept was actually called
                    logger.warning(f"[WebSocket] WebSocket application_state: {websocket.application_state if hasattr(websocket, 'application_state') else 'N/A'}")
                    break
                
                # Use receive_text() which handles disconnects automatically
                data = await websocket.receive_text()
                logger.info(f"[WebSocket] Raw data received: {len(data)} bytes")
            except WebSocketDisconnect as e:
                logger.info(f"[WebSocket] Client disconnected: code={e.code}, reason={e.reason}")
                break
            except RuntimeError as e:
                if "not connected" in str(e).lower() or "accept" in str(e).lower():
                    logger.error(f"[WebSocket] WebSocket connection error: {e}")
                    break
                raise
            except Exception as e:
                logger.error(f"[WebSocket] Error receiving text: {e}", exc_info=True)
                # If it's a disconnect/connection error, break the loop
                if any(keyword in str(e).lower() for keyword in ["disconnect", "not connected", "accept", "1001"]):
                    logger.info("[WebSocket] Connection error detected, breaking loop")
                    break
                # Otherwise, try to continue
                continue
            
            try:
                message_data = json.loads(data)
                logger.info(f"[WebSocket] Parsed message: {message_data}")
            except json.JSONDecodeError as e:
                logger.error(f"[WebSocket] Failed to parse JSON: {e}, data: {data}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": f"Invalid JSON: {str(e)}"}
                })
                continue
            
            logger.info(f"[WebSocket] WebSocket message received: {message_data}")
            
            # Send initial acknowledgment
            await websocket.send_json({
                "type": "status",
                "data": {"status": "processing", "message": "Processing your request..."}
            })
            
            # Process through Green Agent (which internally calls White Agent)
            # This avoids duplicate execution - Green Agent orchestrates the full flow
            # Events will be streamed in real-time via the event queue
            logger.info("[WebSocket] Starting Green Agent processing...")
            evaluation_result = None
            white_agent_output = None
            try:
                # Green Agent internally calls White Agent, so we only need one call
                eval_result = await green_agent.process_message(message_data["message"])
                
                logger.info(f"[WebSocket] Green Agent returned keys: {list(eval_result.keys()) if isinstance(eval_result, dict) else 'not dict'}")
                
                # Extract White Agent output from Green Agent result
                # Green Agent's process_message returns: {"message": ..., "agent_type": ..., "conversation_length": ..., "evaluation_result": ...}
                # But we need to get the White Agent's actual response from the state
                if "white_agent_response" in eval_result:
                    white_agent_output = eval_result.get("white_agent_response", "")
                    logger.info(f"[WebSocket] Extracted white_agent_response (length: {len(white_agent_output) if white_agent_output else 0})")
                elif "messages" in eval_result:
                    # Extract last White Agent message from state
                    messages = eval_result.get("messages", [])
                    logger.info(f"[WebSocket] Found {len(messages)} messages in result")
                    white_agent_messages = [m for m in messages if hasattr(m, 'agent_type') and m.agent_type.value == 'white_agent']
                    if white_agent_messages:
                        white_agent_output = white_agent_messages[-1].content
                        logger.info(f"[WebSocket] Extracted from messages (length: {len(white_agent_output) if white_agent_output else 0})")
                    else:
                        logger.warning(f"[WebSocket] No white_agent messages found in {len(messages)} messages")
                elif "message" in eval_result:
                    # Green Agent returns the final message, but we need to check if there's a white_agent_response in the state
                    # Try to get it from the Green Agent's state
                    try:
                        # Access the Green Agent's state to get white_agent_response
                        if hasattr(green_agent, 'state') and 'white_agent_response' in green_agent.state:
                            white_agent_output = green_agent.state.get('white_agent_response', '')
                            logger.info(f"[WebSocket] Extracted white_agent_response from state (length: {len(white_agent_output) if white_agent_output else 0})")
                        else:
                            # Fallback: use the message if it's from white agent (but Green Agent returns its own message)
                            logger.warning(f"[WebSocket] Green Agent returned 'message' but no white_agent_response in state. Using empty string.")
                            white_agent_output = ""  # Green Agent's message is the evaluation summary, not White Agent's response
                    except Exception as e:
                        logger.warning(f"[WebSocket] Error accessing Green Agent state: {e}")
                        white_agent_output = ""
                else:
                    logger.warning(f"[WebSocket] No white_agent_response or messages in eval_result. Keys: {list(eval_result.keys()) if isinstance(eval_result, dict) else 'not dict'}")
                
                if "evaluation_result" in eval_result:
                    evaluation_result = eval_result.get("evaluation_result")
                    logger.info(f"[WebSocket] Evaluation completed. Keys: {evaluation_result.keys() if evaluation_result else 'None'}")
                
                logger.info(f"[WebSocket] Green Agent processing completed. White agent output length: {len(white_agent_output) if white_agent_output else 0}")
            except Exception as e:
                logger.error(f"[WebSocket] Error processing message with Green Agent: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": str(e)}
                })
                return
            
            # Get trace ledger data
            ledger_data = None
            try:
                ledger_data = ledger.get_ledger()
                logger.info(f"[WebSocket] Trace ledger retrieved. Entries: {len(ledger_data.traces) if ledger_data and hasattr(ledger_data, 'traces') else 0}")
            except Exception as e:
                logger.error(f"[WebSocket] Error getting ledger: {e}", exc_info=True)
                ledger_data = None
            
            # Send final response with layered data first (without analysis)
            final_response = {
                "type": "final_response",
                "data": {
                    "white_agent_output": {
                        "message": white_agent_output or "",
                        "agent_type": "white_agent",
                        "conversation_length": 0
                    },
                    "trace_ledger": ledger_data.model_dump(mode='json') if ledger_data else None,
                    "trace_analysis": None,  # Will be sent separately after analysis
                    "evaluation_result": evaluation_result
                }
            }
            logger.info(f"[WebSocket] Sending final response. Message length: {len(final_response['data']['white_agent_output']['message'])}")
            
            # Check if WebSocket is still connected before sending
            try:
                current_state = websocket.client_state.name if hasattr(websocket.client_state, 'name') else str(websocket.client_state)
                if current_state != "CONNECTED":
                    logger.warning(f"[WebSocket] Cannot send final response, WebSocket not connected: {current_state}")
                else:
                    await websocket.send_json(final_response)
                    logger.info("[WebSocket] Final response sent successfully")
                    # Mark final response sent so late tool/trace events are ignored
                    final_response_sent = True
            except (WebSocketDisconnect, RuntimeError) as e:
                error_str = str(e)
                if "close" in error_str.lower() or "not connected" in error_str.lower():
                    logger.warning(f"[WebSocket] Connection closed before final response could be sent: {error_str}")
                else:
                    logger.error(f"[WebSocket] Error sending final response: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"[WebSocket] Unexpected error sending final response: {e}", exc_info=True)
            
            # ============================================================
            # FINAL STEP: Analyze backend logs with LLM
            # This runs ONLY ONCE at the very end, after all tool execution is complete
            # ============================================================
            trace_analysis = None
            try:
                # Wait for logs to flush completely - all tool calls should be done by now
                import asyncio
                await asyncio.sleep(1.0)  # Give logs time to flush to disk
                
                # Force log flush if possible
                import sys
                import logging
                for handler in logging.root.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()
                
                from green_agent.analysis.trace_analyzer import analyze_backend_logs
                logger.info("[WebSocket] ===== STARTING BACKEND LOG ANALYSIS (FINAL STEP) =====")
                logger.info("[WebSocket] All tool execution complete. Analyzing logs to extract detailed action breakdown...")
                
                # Extract tool names from trace ledger if available (more reliable than log parsing)
                tool_names_from_ledger = set()
                if ledger_data and hasattr(ledger_data, 'traces'):
                    for trace in ledger_data.traces:
                        if hasattr(trace, 'tool_name') and trace.tool_name:
                            tool_names_from_ledger.add(trace.tool_name)
                    logger.info(f"[WebSocket] Tools identified from trace ledger: {tool_names_from_ledger}")
                
                # Analyze the backend logs to extract detailed action breakdown
                # This looks at AgentExecutor's Thought/Action/Observation cycles
                # Pass tool names from ledger to help with detection
                trace_analysis = analyze_backend_logs(
                    log_lines=2000,  # Get more lines for complete context
                    known_tools=tool_names_from_ledger if tool_names_from_ledger else None
                )
                
                logger.info(f"[WebSocket] Backend log analysis completed successfully.")
                if isinstance(trace_analysis, dict):
                    if 'error' in trace_analysis:
                        logger.warning(f"[WebSocket] Analysis error: {trace_analysis['error']}")
                    else:
                        # Check if it's grouped by tool or single analysis
                        tool_keys = [k for k in trace_analysis.keys() if k not in ['error', 'summary', 'tool_calls', 'dataframe_operations', 'analysis_steps', 'key_insights', 'detailed_actions']]
                        if tool_keys:
                            logger.info(f"[WebSocket] Analysis grouped by {len(tool_keys)} tools: {tool_keys}")
                        else:
                            logger.info(f"[WebSocket] Single analysis result with keys: {list(trace_analysis.keys())}")
                logger.info("[WebSocket] ===== BACKEND LOG ANALYSIS COMPLETE =====")
                
                # Send analysis update as a separate message (new layer)
                if trace_analysis:
                    try:
                        # Check if WebSocket is still connected
                        current_state = websocket.client_state.name if hasattr(websocket.client_state, 'name') else str(websocket.client_state)
                        if current_state == "CONNECTED":
                            analysis_update = {
                                "type": "trace_analysis_update",
                                "data": {
                                    "trace_analysis": trace_analysis
                                }
                            }
                            await websocket.send_json(analysis_update)
                            logger.info("[WebSocket] Trace analysis update sent to client")
                        else:
                            logger.warning(f"[WebSocket] Cannot send trace analysis, WebSocket not connected: {current_state}")
                    except (WebSocketDisconnect, RuntimeError) as e:
                        error_str = str(e)
                        if "close" in error_str.lower() or "not connected" in error_str.lower():
                            logger.warning(f"[WebSocket] Connection closed before trace analysis could be sent: {error_str}")
                        else:
                            logger.error(f"[WebSocket] Error sending trace analysis: {e}", exc_info=True)
                    except Exception as e:
                        logger.error(f"[WebSocket] Unexpected error sending trace analysis: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"[WebSocket] Error analyzing backend logs: {e}", exc_info=True)
                # Don't send error - analysis is optional and shouldn't break the flow
            
    except WebSocketDisconnect as e:
        logger.info(f"[WebSocket] Client disconnected: {e}")
    except Exception as e:
        logger.error(f"[WebSocket] WebSocket error: {e}", exc_info=True)
    finally:
        # Unsubscribe from event queue
        try:
            if 'event_queue' in locals() and 'send_event' in locals():
                event_queue.unsubscribe(send_event)
                logger.debug("[WebSocket] Unsubscribed from event queue")
        except Exception as e:
            logger.debug(f"[WebSocket] Error unsubscribing (may already be removed): {e}")
        
        # Clean up connection
        if websocket in manager.active_connections:
            manager.active_connections.remove(websocket)
        logger.info(f"[WebSocket] Connection cleaned up. Total: {len(manager.active_connections)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

