# Quick Start with Ngrok

Run your Green Agent app with ngrok tunnel for public access.

## 🚀 Quick Start

### Option 1: Automated Script (Recommended)

```bash
./run_with_ngrok.sh
```

This will:
1. Start the backend server on port 8001
2. Start ngrok tunnel
3. Show you the public URLs

Then in another terminal:
```bash
cd frontend
# Get the ngrok URL from the script output, then:
VITE_API_URL=https://your-ngrok-url.ngrok-free.app \
VITE_WS_URL=wss://your-ngrok-url.ngrok-free.app \
npm run dev
```

### Option 2: Manual Steps

#### 1. Start Backend with Ngrok Support

```bash
cd backend
source ../venv/bin/activate
ENABLE_NGROK=true python api_server.py
```

#### 2. Start Ngrok (in another terminal)

```bash
ngrok http 8001
```

You'll see output like:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8001
```

#### 3. Start Frontend with Ngrok URL

```bash
cd frontend
VITE_API_URL=https://abc123.ngrok-free.app \
VITE_WS_URL=wss://abc123.ngrok-free.app \
npm run dev
```

**Note:** Replace `abc123.ngrok-free.app` with your actual ngrok URL.

## 🔍 Get Your Ngrok URL

After starting ngrok, you can get the URL:

```bash
curl -s http://localhost:4040/api/tunnels | python3 -m json.tool | grep public_url
```

Or visit: http://localhost:4040

## ✅ Test Your Setup

1. **Backend Health Check:**
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/health
   ```

2. **Frontend:**
   - Open http://localhost:5173
   - The frontend will connect to your ngrok backend

## 🛑 Stop Everything

```bash
# Stop backend
pkill -f "api_server.py"

# Stop ngrok
pkill -f "ngrok"

# Stop frontend
# Press Ctrl+C in the frontend terminal
```

## 📝 Environment Variables

The frontend uses these environment variables:
- `VITE_API_URL` - HTTP/HTTPS API URL (default: http://localhost:8001)
- `VITE_WS_URL` - WebSocket URL (default: ws://localhost:8001)

## 🔧 Troubleshooting

- **CORS errors:** Make sure `ENABLE_NGROK=true` is set when starting backend
- **Connection refused:** Ensure backend is running on port 8001
- **WebSocket errors:** Make sure you use `wss://` (not `ws://`) for HTTPS ngrok URLs

