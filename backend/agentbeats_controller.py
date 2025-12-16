"""
Custom AgentBeats-compatible controller for Python 3.12+
This provides the same functionality as the earthshaker package's agentbeats controller
but works with Python 3.12.
"""
import asyncio
import os
import sys
import signal
import subprocess
import logging
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentProcess:
    """Manages a single agent process."""
    
    def __init__(self, agent_id: str, run_script: str, agent_port: int, host: str = "0.0.0.0", public_url: str = None):
        self.agent_id = agent_id
        self.run_script = run_script
        self.agent_port = agent_port
        self.host = host
        self.public_url = public_url  # Public URL (e.g., ngrok URL)
        self.process: Optional[subprocess.Popen] = None
        self.state = "stopped"
        self.started_at: Optional[datetime] = None
        self.logs: list = []
        
    def start(self) -> bool:
        """Start the agent process."""
        if self.process and self.process.poll() is None:
            logger.warning(f"Agent {self.agent_id} is already running")
            return False
            
        try:
            # Set environment variables for the agent
            env = os.environ.copy()
            env["HOST"] = self.host
            env["AGENT_PORT"] = str(self.agent_port)
            
            # CRITICAL: Pass the public URL so the agent card contains the correct URL
            # Without this, the agent card will contain http://0.0.0.0:8001 which
            # AgentBeats (running remotely) cannot reach!
            if self.public_url:
                env["AGENT_URL"] = self.public_url
            
            # Start the process
            self.process = subprocess.Popen(
                ["bash", self.run_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.state = "starting"
            self.started_at = datetime.now()
            logger.info(f"Started agent {self.agent_id} with PID {self.process.pid}")
            
            # Use threading instead of asyncio for monitoring
            import threading
            threading.Thread(target=self._monitor_startup_sync, daemon=True).start()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self.state = "error"
            return False
    
    def _monitor_startup_sync(self):
        """Monitor agent startup and update state (synchronous version)."""
        import time
        time.sleep(2)  # Wait for startup
        if self.process and self.process.poll() is None:
            self.state = "running"
            logger.info(f"Agent {self.agent_id} is now running")
        else:
            self.state = "error"
            logger.error(f"Agent {self.agent_id} failed to start")
    
    def stop(self) -> bool:
        """Stop the agent process."""
        if not self.process:
            return False
            
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.state = "stopped"
            logger.info(f"Stopped agent {self.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            return False
    
    def reset(self) -> bool:
        """Reset the agent by restarting it."""
        self.stop()
        return self.start()
    
    def get_status(self) -> Dict:
        """Get current agent status."""
        # Use public URL if available, otherwise use local
        # Note: Use base URL (not /to_agent/{id}) because A2A JSON-RPC handler is at /
        if self.public_url:
            agent_url = self.public_url.rstrip('/')
        else:
            agent_url = f"http://{self.host}:{self.agent_port}"
        
        return {
            "id": self.agent_id,
            "state": self.state,
            "url": agent_url,
            "internal_port": self.agent_port,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "pid": self.process.pid if self.process else None
        }


class AgentBeatsController:
    """AgentBeats-compatible controller for managing agents."""
    
    def __init__(self, controller_port: int = 8101):
        self.controller_port = controller_port
        self.agents: Dict[str, AgentProcess] = {}
        self.app = self._create_app()
        
    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(title="AgentBeats Controller", version="1.0.0")
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        app.add_api_route("/", self.root, methods=["GET"])
        app.add_api_route("/", self.proxy_jsonrpc, methods=["POST"])  # Proxy JSON-RPC POST to agent
        app.add_api_route("/status", self.status, methods=["GET"])
        app.add_api_route("/agents", self.list_agents, methods=["GET"])
        app.add_api_route("/agents/{agent_id}", self.get_agent, methods=["GET"])
        app.add_api_route("/agents/{agent_id}/reset", self.reset_agent, methods=["POST"])
        app.add_api_route("/agents/{agent_id}/start", self.start_agent, methods=["POST"])
        app.add_api_route("/agents/{agent_id}/stop", self.stop_agent, methods=["POST"])
        
        # Proxy A2A protocol requests to the actual agent
        app.add_api_route("/to_agent/{agent_id:path}", self.proxy_to_agent, methods=["GET", "POST", "HEAD"])
        app.add_api_route("/.well-known/agent-card.json", self.proxy_agent_card, methods=["GET"])
        
        return app
    
    def register_agent(self, agent_id: str, run_script: str, agent_port: int, host: str = "0.0.0.0", public_url: str = None):
        """Register a new agent."""
        agent = AgentProcess(agent_id, run_script, agent_port, host, public_url)
        self.agents[agent_id] = agent
        logger.info(f"Registered agent {agent_id} (port {agent_port})")
        if public_url:
            logger.info(f"Public URL: {public_url}")
        
    async def root(self):
        """Root endpoint with management UI."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgentBeats Controller</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .agent-card {{
                    background: white;
                    padding: 20px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .status {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .status.running {{ background: #10b981; color: white; }}
                .status.stopped {{ background: #ef4444; color: white; }}
                .status.starting {{ background: #f59e0b; color: white; }}
                .status.error {{ background: #dc2626; color: white; }}
                button {{
                    padding: 8px 16px;
                    margin: 4px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 500;
                }}
                .btn-primary {{ background: #3b82f6; color: white; }}
                .btn-danger {{ background: #ef4444; color: white; }}
                .btn-success {{ background: #10b981; color: white; }}
                button:hover {{ opacity: 0.9; }}
                .info {{ color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 AgentBeats Controller</h1>
                <p>Manage and monitor your A2A agents</p>
            </div>
            
            <div id="agents"></div>
            
            <script>
                async function loadAgents() {{
                    const response = await fetch('/agents');
                    const agents = await response.json();
                    
                    const container = document.getElementById('agents');
                    container.innerHTML = '';
                    
                    for (const [id, agent] of Object.entries(agents)) {{
                        const card = document.createElement('div');
                        card.className = 'agent-card';
                        card.innerHTML = `
                            <h2>Agent: ${{id}}</h2>
                            <p><span class="status ${{agent.state}}">${{agent.state.toUpperCase()}}</span></p>
                            <p class="info">Port: ${{agent.internal_port}} | URL: <a href="${{agent.url}}" target="_blank">${{agent.url}}</a></p>
                            <p class="info">PID: ${{agent.pid || 'N/A'}} | Started: ${{agent.started_at || 'N/A'}}</p>
                            <div>
                                <button class="btn-success" onclick="startAgent('${{id}}')">▶️ Start</button>
                                <button class="btn-danger" onclick="stopAgent('${{id}}')">⏹️ Stop</button>
                                <button class="btn-primary" onclick="resetAgent('${{id}}')">🔄 Reset</button>
                                <a href="${{agent.url}}/.well-known/agent-card.json" target="_blank">
                                    <button class="btn-primary">📋 Agent Card</button>
                                </a>
                            </div>
                        `;
                        container.appendChild(card);
                    }}
                }}
                
                async function startAgent(id) {{
                    await fetch(`/agents/${{id}}/start`, {{ method: 'POST' }});
                    setTimeout(loadAgents, 1000);
                }}
                
                async function stopAgent(id) {{
                    await fetch(`/agents/${{id}}/stop`, {{ method: 'POST' }});
                    setTimeout(loadAgents, 1000);
                }}
                
                async function resetAgent(id) {{
                    await fetch(`/agents/${{id}}/reset`, {{ method: 'POST' }});
                    setTimeout(loadAgents, 1000);
                }}
                
                // Load agents initially and refresh every 5 seconds
                loadAgents();
                setInterval(loadAgents, 5000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    async def status(self):
        """Controller status endpoint."""
        running_count = sum(1 for agent in self.agents.values() if agent.state == "running")
        return JSONResponse({
            "maintained_agents": len(self.agents),
            "running_agents": running_count,
            "controller_port": self.controller_port
        })
    
    async def list_agents(self):
        """List all agents."""
        return JSONResponse({
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        })
    
    async def get_agent(self, agent_id: str):
        """Get specific agent status."""
        if agent_id not in self.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        return JSONResponse(self.agents[agent_id].get_status())
    
    async def reset_agent(self, agent_id: str):
        """Reset an agent."""
        if agent_id not in self.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        success = self.agents[agent_id].reset()
        return JSONResponse({
            "status": "ok" if success else "error",
            "message": "Agent reset successfully" if success else "Failed to reset agent"
        })
    
    async def start_agent(self, agent_id: str):
        """Start an agent."""
        if agent_id not in self.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        success = self.agents[agent_id].start()
        return JSONResponse({
            "status": "ok" if success else "error",
            "message": "Agent started" if success else "Failed to start agent"
        })
    
    async def stop_agent(self, agent_id: str):
        """Stop an agent."""
        if agent_id not in self.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        success = self.agents[agent_id].stop()
        return JSONResponse({
            "status": "ok" if success else "error",
            "message": "Agent stopped" if success else "Failed to stop agent"
        })
    
    async def proxy_to_agent(self, agent_id: str, request: Request):
        """Proxy A2A protocol requests to the actual agent."""
        # Get the first agent (we only have one per controller)
        if not self.agents:
            raise HTTPException(status_code=404, detail="No agents registered")
        
        agent = list(self.agents.values())[0]
        
        # Build target URL (agent runs on its internal port)
        path = request.url.path
        
        # For POST requests (JSON-RPC), proxy to root "/" where the handler is
        # For GET requests (agent card, etc.), use the original path
        if request.method == "POST":
            target_url = f"http://localhost:{agent.agent_port}/"
        else:
            target_url = f"http://localhost:{agent.agent_port}{path}"
            
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"
        
        logger.info(f"Proxying A2A request: {request.method} {path} -> {target_url}")
        
        # Get request body
        body = await request.body()
        
        # Forward the request
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=dict(request.headers),
                    content=body,
                    follow_redirects=False
                )
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
            except httpx.ConnectError:
                raise HTTPException(status_code=503, detail="Agent not available")
            except Exception as e:
                logger.error(f"Proxy error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def proxy_agent_card(self, request: Request):
        """Proxy agent card request to the actual agent."""
        if not self.agents:
            raise HTTPException(status_code=404, detail="No agents registered")
        
        agent = list(self.agents.values())[0]
        target_url = f"http://localhost:{agent.agent_port}/.well-known/agent-card.json"
        
        logger.info(f"Proxying agent card request to {target_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(target_url)
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )
            except Exception as e:
                logger.error(f"Failed to get agent card: {e}")
                raise HTTPException(status_code=503, detail="Agent card not available")
    
    async def proxy_jsonrpc(self, request: Request):
        """Proxy JSON-RPC POST requests to the actual agent (for A2A protocol)."""
        if not self.agents:
            raise HTTPException(status_code=404, detail="No agents registered")
        
        agent = list(self.agents.values())[0]
        target_url = f"http://localhost:{agent.agent_port}/"
        
        # Get request body
        body = await request.body()
        
        logger.info(f"Proxying JSON-RPC POST to {target_url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    target_url,
                    headers={"Content-Type": "application/json"},
                    content=body,
                )
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
            except httpx.ConnectError:
                raise HTTPException(status_code=503, detail="Agent not available")
            except Exception as e:
                logger.error(f"JSON-RPC proxy error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, host: str = "0.0.0.0"):
        """Run the controller."""
        logger.info(f"Starting AgentBeats Controller on {host}:{self.controller_port}")
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Shutting down controller and agents...")
            for agent in self.agents.values():
                agent.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the app
        uvicorn.run(self.app, host=host, port=self.controller_port)


def main():
    """Main entry point for the controller."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentBeats Controller")
    parser.add_argument("--port", type=int, default=8101, help="Controller port")
    parser.add_argument("--host", default="0.0.0.0", help="Controller host")
    parser.add_argument("--public-url", default=None, help="Public URL (e.g., ngrok URL)")
    args = parser.parse_args()
    
    # Detect role and setup agent
    role = os.getenv("ROLE", "")
    agent_port = int(os.getenv("AGENT_PORT", "8001"))
    agent_host = os.getenv("HOST", "0.0.0.0")
    public_url = args.public_url or os.getenv("PUBLIC_URL")
    
    if not role:
        logger.error("ROLE environment variable not set. Use ROLE=green or ROLE=white")
        sys.exit(1)
    
    # Create controller
    controller = AgentBeatsController(controller_port=args.port)
    
    # Find the run script based on role
    script_path = f"./run_{role}.sh"
    if not os.path.exists(script_path):
        logger.error(f"Run script not found: {script_path}")
        sys.exit(1)
    
    # Register and start the agent
    agent_id = f"{role}_agent"
    controller.register_agent(agent_id, script_path, agent_port, agent_host, public_url)
    controller.agents[agent_id].start()
    
    # Run the controller
    controller.run(host=args.host)


if __name__ == "__main__":
    main()


