# Cloudflare Temporary Tunnels - Quick Setup

Simple temporary HTTPS URLs for White Agent and Green Agent that last for **several hours** (typically 2-8 hours).

## 🚀 Quick Start

### Option 1: Start Both Tunnels Together

```bash
./start_cloudflare_both.sh
```

This will start both tunnels and show you the URLs.

### Option 2: Start Tunnels Separately

**Terminal 1 - White Agent:**
```bash
./start_cloudflare_white_agent.sh
```

**Terminal 2 - Green Agent:**
```bash
./start_cloudflare_green_agent.sh
```

## 📋 Prerequisites

1. **Install cloudflared:**
   ```bash
   brew install cloudflared  # macOS
   # or
   sudo apt-get install cloudflared  # Linux
   ```

2. **Start your backend servers:**

   **Terminal 1 - White Agent:**
   ```bash
   cd backend
   source ../venv/bin/activate
   ENABLE_NGROK=true PORT=8002 python white_agent_server.py
   ```

   **Terminal 2 - Green Agent:**
   ```bash
   cd backend
   source ../venv/bin/activate
   ENABLE_NGROK=true python api_server.py
   ```

3. **Start the tunnels** (use Option 1 or 2 above)

## ✅ What You Get

After running the scripts, you'll see output like:

```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at:                                         |
|  https://blue-mountain-9372.trycloudflare.com                                             |
+--------------------------------------------------------------------------------------------+
```

**Copy those URLs** - they're your temporary HTTPS endpoints!

## 🌐 Using the URLs

### White Agent
- **URL**: `https://xxxxx.trycloudflare.com` (from White Agent tunnel)
- **Health Check**: `https://xxxxx.trycloudflare.com/health`
- **API**: `https://xxxxx.trycloudflare.com/api/chat`

### Green Agent
- **URL**: `https://xxxxx.trycloudflare.com` (from Green Agent tunnel)
- **Health Check**: `https://xxxxx.trycloudflare.com/health`
- **API**: `https://xxxxx.trycloudflare.com/api/chat/green`
- **WebSocket**: `wss://xxxxx.trycloudflare.com/ws/green`

## ⏱️ Tunnel Duration

- **Typical duration**: 2-8 hours
- **No login required**: Works immediately
- **New URL each time**: Each restart gets a new URL
- **Free**: No Cloudflare account needed

## 🔍 Verify It's Working

```bash
# Check White Agent
curl https://your-white-agent-url.trycloudflare.com/health

# Check Green Agent
curl https://your-green-agent-url.trycloudflare.com/health
```

## 🛑 Stop Tunnels

Press `Ctrl+C` in the terminal where the tunnel is running, or:

```bash
pkill -f "cloudflared tunnel"
```

## 📝 Notes

- **URLs change**: Each time you restart, you get a new URL
- **Keep running**: Keep both the backend server and tunnel running
- **WebSocket**: Use `wss://` (not `ws://`) for secure WebSocket connections
- **CORS**: Both servers automatically allow Cloudflare domains when `ENABLE_NGROK=true`

## 🆚 Temporary vs Permanent

| Feature | Temporary (This) | Permanent |
|---------|----------------|-----------|
| Setup | ✅ Instant | Requires config |
| Duration | 2-8 hours | Forever |
| URL | Changes each restart | Same URL |
| Login | ❌ Not needed | ✅ Required |
| DNS | ❌ Not needed | ✅ Required |
| Use Case | Testing/Development | Production |

## 🐛 Troubleshooting

### "Connection refused"
- Make sure your backend server is running on the correct port
- Check: `lsof -i :8001` (Green Agent) or `lsof -i :8002` (White Agent)

### "Tunnel not found"
- Wait a few seconds for the tunnel to initialize
- Check the log output for the URL

### Port already in use
```bash
# Kill processes on ports
lsof -ti:8001 | xargs kill -9  # Green Agent
lsof -ti:8002 | xargs kill -9  # White Agent
```

