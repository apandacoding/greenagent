# Cloudflare Tunnel Setup for Green Agent

Expose your Green Agent backend using Cloudflare's free tunnel service (cloudflared).

## 🚀 Quick Setup

### Step 1: Install cloudflared

**macOS:**
```bash
brew install cloudflared
```

**Linux:**
```bash
sudo apt-get install cloudflared
```

**Windows:**
Download from: https://github.com/cloudflare/cloudflared/releases

### Step 2: Start your backend (if not already running)

Your backend runs on **port 8001**:

```bash
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true python api_server.py
```

Or with uvicorn directly:
```bash
cd backend
uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```

### Step 3: Run cloudflared tunnel

Open a **new terminal** and run:

```bash
cloudflared tunnel --url http://localhost:8001
```

You'll get output like:
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |
|  https://blue-mountain-9372.trycloudflare.com                                             |
+--------------------------------------------------------------------------------------------+
```

**Copy that URL** - this is your public backend URL!

### Step 4: Use the URL

**For frontend:**
```bash
cd frontend
VITE_API_URL=https://blue-mountain-9372.trycloudflare.com \
VITE_WS_URL=wss://blue-mountain-9372.trycloudflare.com \
npm run dev
```

**For AgentBeats or other services:**
```python
GREEN_AGENT_URL = "https://blue-mountain-9372.trycloudflare.com"
```

## 🔄 Important Notes

- **Port**: Your backend uses **port 8001**, not 8000
- **URL changes**: Each time you restart cloudflared, you get a new URL
- **WebSocket**: Use `wss://` (not `ws://`) for WebSocket connections over HTTPS
- **Keep running**: Keep both the backend and cloudflared running

## 🆚 Cloudflare vs Ngrok

| Feature | Cloudflare | Ngrok |
|---------|-----------|-------|
| Free tier | ✅ Yes | ✅ Yes |
| URL changes | ✅ Each restart | ✅ Each restart |
| Speed | Fast | Fast |
| Setup | Simple | Simple |
| WebSocket | ✅ Supported | ✅ Supported |

Both work great! Use whichever you prefer.

## 🛑 Stop Everything

```bash
# Stop backend
pkill -f api_server.py

# Stop cloudflared
# Press Ctrl+C in the cloudflared terminal
```

