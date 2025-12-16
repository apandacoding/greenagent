"""
Simple reverse proxy to route both green and white agents through one ngrok tunnel.
Routes:
  /green/* -> localhost:8101 (Green Agent Controller)
  /white/* -> localhost:8102 (White Agent Controller)
  / -> Shows available agents
"""
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentBeats Multi-Agent Proxy")

# Target controllers
GREEN_CONTROLLER = "http://localhost:8101"
WHITE_CONTROLLER = "http://localhost:8102"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy(path: str, request: Request):
    """Proxy requests to appropriate controller."""
    
    # Root path - show info
    if not path or path == "/":
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>AgentBeats Multi-Agent Proxy</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🎯 AgentBeats Multi-Agent Proxy</h1>
            <p>This proxy routes requests to multiple agents through a single ngrok URL.</p>
            <h2>Available Agents:</h2>
            <ul>
                <li><strong>Green Agent (Assessor):</strong> 
                    <a href="/green/status">/green/status</a> | 
                    <a href="/green/agents">/green/agents</a>
                </li>
                <li><strong>White Agent (Task Executor):</strong> 
                    <a href="/white/status">/white/status</a> | 
                    <a href="/white/agents">/white/agents</a>
                </li>
            </ul>
            <h2>For AgentBeats Registration:</h2>
            <ul>
                <li><strong>Green Controller URL:</strong> <code>https://your-ngrok-url.ngrok-free.app/green</code></li>
                <li><strong>White Controller URL:</strong> <code>https://your-ngrok-url.ngrok-free.app/white</code></li>
            </ul>
        </body>
        </html>
        """)
    
    # Route based on path prefix
    if path.startswith("green/") or path.startswith("green"):
        target = GREEN_CONTROLLER
        # Remove 'green' prefix
        path = path[6:] if path.startswith("green/") else path[5:]  # 'green/' is 6 chars, 'green' is 5
    elif path.startswith("white/") or path.startswith("white"):
        target = WHITE_CONTROLLER
        # Remove 'white' prefix
        path = path[6:] if path.startswith("white/") else path[5:]  # 'white/' is 6 chars, 'white' is 5
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Unknown agent. Use /green/* or /white/*"}
        )
    
    # Strip leading slash to avoid double slash in URL
    path = path.lstrip("/")
    
    # Build target URL
    url = f"{target}/{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    
    logger.info(f"Proxying {request.method} {request.url.path} -> {url}")
    
    # Get request body if present
    body = await request.body()
    
    # Forward the request
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=dict(request.headers),
                content=body,
                follow_redirects=False
            )
            
            # Return proxied response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=503,
                content={"error": f"Controller not available at {target}"}
            )
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )

if __name__ == "__main__":
    print("=" * 50)
    print("AgentBeats Multi-Agent Proxy Starting...")
    print("=" * 50)
    print("Green Agent Controller: http://localhost:8101")
    print("White Agent Controller: http://localhost:8102")
    print("Proxy Server: http://localhost:8100")
    print("=" * 50)
    print("\nRoutes:")
    print("  /green/* -> Green Agent")
    print("  /white/* -> White Agent")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8100)


