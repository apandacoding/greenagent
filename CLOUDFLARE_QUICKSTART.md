# Cloudflare Tunnel Quick Start

## 🚀 Fast Setup (5 minutes)

### 1. Install cloudflared
```bash
brew install cloudflared  # macOS
# or
sudo apt-get install cloudflared  # Linux
```

### 2. Run Setup
```bash
./setup_cloudflare_tunnels.sh
```

This will:
- ✅ Login to Cloudflare (browser opens)
- ✅ Create tunnel
- ✅ Set up DNS (if you choose)

### 3. Edit Config
Edit `cloudflare-config.yml` and replace `yourdomain.com` with your domain.

### 4. Start Everything
```bash
./start_backend_with_cloudflare.sh
```

## ✅ That's It!

Your agents are now available at:
- **White Agent**: `https://white-agent.yourdomain.com`
- **Green Agent**: `https://green-agent.yourdomain.com`

## 📝 Manual Steps (if needed)

### Set DNS Manually

If you need to set DNS manually:

1. Get tunnel ID:
   ```bash
   cloudflared tunnel list
   ```

2. In Cloudflare Dashboard → DNS, add:
   - `white-agent` → CNAME → `{tunnel-id}.cfargotunnel.com` (Proxied ✅)
   - `green-agent` → CNAME → `{tunnel-id}.cfargotunnel.com` (Proxied ✅)

### Start Servers Separately

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

**Terminal 3 - Tunnel:**
```bash
./start_cloudflare_tunnels.sh
```

## 🔍 Verify

```bash
# Check backend servers
curl http://localhost:8002/health  # White Agent
curl http://localhost:8001/health  # Green Agent

# Check Cloudflare URLs
curl https://white-agent.yourdomain.com/health
curl https://green-agent.yourdomain.com/health
```

## 🛑 Stop

Press `Ctrl+C` or:
```bash
pkill -f cloudflared
pkill -f white_agent_server.py
pkill -f api_server.py
```

## 📚 Full Documentation

See `CLOUDFLARE_SETUP.md` for detailed documentation.

