# Ngrok Setup for AgentBeats

This guide shows how to set up your Green Agent with ngrok for AgentBeats integration.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./start_backend_with_ngrok.sh
```

This will:
1. Start both White Agent (port 8002) and Green Agent (port 8001)
2. Start ngrok tunnels for both
3. Display the public URLs and environment variables

### Option 2: Manual Setup

**Terminal 1 - Start Green Agent:**
```bash
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true python api_server.py
```

**Terminal 2 - Start ngrok:**
```bash
ngrok http 8001
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

**Terminal 3 - Set environment variables:**
```bash
export AGENT_URL=https://abc123.ngrok-free.app
export CLOUDRUN_HOST=abc123.ngrok-free.app
export HTTPS_ENABLED=true
```

Then restart the Green Agent with these env vars set.

## 📋 Required Endpoints

Your agent must expose these endpoints:

1. **Agent Card (Primary):**
   ```
   GET /.well-known/agent-card.json
   GET /.well-known/agent.json
   ```

2. **Agent Card with ID:**
   ```
   GET /to_agent/{agent_id}/.well-known/agent-card.json
   GET /to_agent/{agent_id}/.well-known/agent.json
   ```

3. **Controller Endpoint:**
   ```
   GET /to_agent/{agent_id}
   ```

4. **Assessment Endpoint:**
   ```
   POST /assess
   ```

## 🔧 Environment Variables

The agent reads its public URL from these environment variables (in priority order):

1. **AGENT_URL** (highest priority)
   ```bash
   export AGENT_URL=https://your-ngrok-url.ngrok-free.app
   ```

2. **CLOUDRUN_HOST + HTTPS_ENABLED**
   ```bash
   export CLOUDRUN_HOST=your-ngrok-url.ngrok-free.app
   export HTTPS_ENABLED=true
   ```

3. **Request base_url** (fallback, uses the incoming request URL)

## ✅ Verification

### 1. Check Agent Card at Root
```bash
curl https://your-ngrok-url.ngrok-free.app/.well-known/agent-card.json
```

Should return A2A protocol format with `url` field set.

### 2. Check Agent Card with Agent ID
```bash
curl https://your-ngrok-url.ngrok-free.app/to_agent/YOUR_AGENT_ID/.well-known/agent-card.json
```

Should return the same format with `url` pointing to `/to_agent/{agent_id}`.

### 3. Check Controller Endpoint
```bash
curl https://your-ngrok-url.ngrok-free.app/to_agent/YOUR_AGENT_ID
```

Should return agent card.

## 🎯 AgentBeats Configuration

In AgentBeats, set:

**Controller URL:**
```
https://your-ngrok-url.ngrok-free.app/to_agent/YOUR_AGENT_ID
```

**Agent ID:**
```
YOUR_AGENT_ID (from AgentBeats dashboard)
```

## 📝 Important Notes

1. **Agent Card Location:** The platform expects the agent card at `/to_agent/{agent_id}/.well-known/agent-card.json`, not just at root.

2. **Public URL:** The agent must know its public URL. Set `AGENT_URL` or `CLOUDRUN_HOST` environment variables.

3. **HTTPS Required:** AgentBeats requires HTTPS. Use ngrok's HTTPS URL (not HTTP).

4. **Ngrok Free Tier:** 
   - URLs change each restart
   - 4-6 minute connection timeouts
   - Request limits

5. **For Production:** Consider ngrok paid plan for static URLs or use Cloudflare tunnels.

## 🐛 Troubleshooting

### Agent Card Not Loading

1. **Check environment variables:**
   ```bash
   echo $AGENT_URL
   echo $CLOUDRUN_HOST
   echo $HTTPS_ENABLED
   ```

2. **Verify agent card endpoint:**
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/to_agent/YOUR_AGENT_ID/.well-known/agent-card.json
   ```

3. **Check agent card format:**
   - Must have `url` field
   - Must follow A2A protocol 0.3.0
   - Must be valid JSON

### Connection Timeouts

Ngrok free tier has 4-6 minute timeouts. For longer tasks, consider:
- Ngrok paid plan
- Cloudflare tunnels
- Self-hosted solution

### CORS Issues

Make sure `ENABLE_NGROK=true` is set when starting the backend.

## 🔄 Migration from Cloudflare

If you were using Cloudflare tunnels:

1. Stop Cloudflare tunnel
2. Start ngrok tunnel
3. Update environment variables with ngrok URL
4. Restart backend server

The agent will automatically use the new URL from environment variables.

