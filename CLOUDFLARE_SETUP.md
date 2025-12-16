# Cloudflare Tunnel Setup for Green Agent & White Agent

Expose both your Green Agent and White Agent backends using Cloudflare's permanent tunnel service (cloudflared) with **fixed HTTPS URLs**.

## 🎯 Overview

This setup creates **permanent HTTPS URLs** for both agents:
- **White Agent**: `https://white-agent.yourdomain.com` (port 8002)
- **Green Agent**: `https://green-agent.yourdomain.com` (port 8001)

## 📋 Prerequisites

1. **Cloudflare Account**: Free account works fine
2. **Domain**: A domain managed by Cloudflare (free domains work)
3. **cloudflared**: Tunnel client installed locally

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

### Step 2: Run Setup Script

```bash
./setup_cloudflare_tunnels.sh
```

This script will:
1. ✅ Authenticate with Cloudflare (opens browser)
2. ✅ Create a named tunnel
3. ✅ Optionally set up DNS automatically
4. ✅ Guide you through configuration

### Step 3: Configure Your Domain

Edit `cloudflare-config.yml` and update the hostnames:

```yaml
tunnel: green-agent-tunnel
credentials-file: /Users/aryanpanda/green-agent/.cloudflared/green-agent-tunnel.json

ingress:
  # White Agent (port 8002)
  - hostname: white-agent.yourdomain.com  # ← Change this
    service: http://localhost:8002
  # Green Agent (port 8001)  
  - hostname: green-agent.yourdomain.com  # ← Change this
    service: http://localhost:8001
  # Catch-all rule (must be last)
  - service: http_status:404
```

Replace `yourdomain.com` with your actual domain.

### Step 4: Set Up DNS

#### Option A: Automatic (Recommended)

If you ran the setup script with automatic DNS, you're done!

#### Option B: Manual DNS Setup

1. Go to your Cloudflare Dashboard → DNS
2. Get your tunnel ID:
   ```bash
   cloudflared tunnel list
   ```
3. Add CNAME records:
   - **Name**: `white-agent`
   - **Target**: `{tunnel-id}.cfargotunnel.com`
   - **Proxy status**: Proxied (orange cloud) ✅
   
   - **Name**: `green-agent`
   - **Target**: `{tunnel-id}.cfargotunnel.com`
   - **Proxy status**: Proxied (orange cloud) ✅

### Step 5: Start Backend Servers

**Option A: Start Everything Together**

```bash
./start_backend_with_cloudflare.sh
```

**Option B: Start Manually**

Terminal 1 - White Agent:
```bash
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true PORT=8002 python white_agent_server.py
```

Terminal 2 - Green Agent:
```bash
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true python api_server.py
```

Terminal 3 - Cloudflare Tunnel:
```bash
./start_cloudflare_tunnels.sh
```

## ✅ Verify Setup

### Check Backend Health

```bash
# White Agent (local)
curl http://localhost:8002/health

# Green Agent (local)
curl http://localhost:8001/health

# White Agent (Cloudflare)
curl https://white-agent.yourdomain.com/health

# Green Agent (Cloudflare)
curl https://green-agent.yourdomain.com/health
```

### Check Tunnel Status

```bash
cloudflared tunnel info green-agent-tunnel
```

## 🌐 Using the URLs

### Frontend Configuration

Update your frontend `.env` or environment variables:

```env
VITE_API_URL=https://green-agent.yourdomain.com
VITE_WS_URL=wss://green-agent.yourdomain.com
WHITE_AGENT_URL=https://white-agent.yourdomain.com
```

### API Endpoints

- **White Agent API**: `https://white-agent.yourdomain.com/api/chat`
- **Green Agent API**: `https://green-agent.yourdomain.com/api/chat/green`
- **White Agent Health**: `https://white-agent.yourdomain.com/health`
- **Green Agent Health**: `https://green-agent.yourdomain.com/health`

### WebSocket Support

Both agents support WebSocket over HTTPS:
- Use `wss://` (not `ws://`) for secure WebSocket connections
- Example: `wss://green-agent.yourdomain.com/ws/green`

## 🔧 Configuration Details

### Tunnel Config File

The `cloudflare-config.yml` file controls:
- Which tunnel to use
- Domain routing (which hostname goes to which port)
- Credentials location

### Ports

- **White Agent**: Port `8002`
- **Green Agent**: Port `8001`

### CORS

Both servers automatically allow Cloudflare domains when `ENABLE_NGROK=true` is set.

## 🛑 Stop Everything

```bash
# Find and kill processes
pkill -f white_agent_server.py
pkill -f api_server.py
pkill -f cloudflared

# Or use Ctrl+C in the terminals where they're running
```

## 🔄 Restart Tunnel

If you need to restart just the tunnel:

```bash
./start_cloudflare_tunnels.sh
```

The tunnel will reconnect automatically and keep the same URLs.

## 📝 Troubleshooting

### Tunnel Won't Start

1. **Check authentication:**
   ```bash
   cloudflared tunnel list
   ```
   Should show your tunnel. If not, run `cloudflared tunnel login` again.

2. **Check DNS:**
   - Ensure DNS records are set to "Proxied" (orange cloud)
   - Wait a few minutes for DNS propagation

3. **Check config:**
   ```bash
   cloudflared tunnel --config cloudflare-config.yml validate
   ```

### 404 Errors

- Make sure backend servers are running on ports 8001 and 8002
- Check that the ingress rules in `cloudflare-config.yml` match your DNS hostnames
- Verify the catch-all rule is last

### Connection Refused

- Verify servers are running: `lsof -i :8001` and `lsof -i :8002`
- Check firewall settings
- Ensure `ENABLE_NGROK=true` is set for CORS

### SSL/TLS Issues

- Cloudflare automatically provides SSL certificates
- Make sure DNS records are "Proxied" (orange cloud), not "DNS only" (grey cloud)
- Wait a few minutes after DNS changes for certificates to provision

## 🆚 Temporary vs Permanent Tunnels

| Feature | Quick Tunnel (`--url`) | Named Tunnel (This Setup) |
|---------|----------------------|--------------------------|
| URL | Changes every restart | **Permanent** ✅ |
| Setup | One command | Requires config |
| DNS | Not needed | Required |
| Production | ❌ No | ✅ Yes |
| HTTPS | ✅ Yes | ✅ Yes |

## 📚 Additional Resources

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Named Tunnel Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/)
- [DNS Configuration](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/routing-to-tunnel/dns/)

## ✨ Benefits of This Setup

✅ **Permanent URLs** - Same URLs every time  
✅ **Free HTTPS** - Automatic SSL certificates  
✅ **Production Ready** - Stable and reliable  
✅ **Easy Management** - Single config file  
✅ **Both Agents** - White and Green in one tunnel  
