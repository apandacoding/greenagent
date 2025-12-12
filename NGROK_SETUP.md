# Ngrok Setup for Green Agent

Quick setup guide for exposing your local backend via ngrok.

## Prerequisites

- ngrok installed (already installed at `/opt/homebrew/bin/ngrok`)
- Backend running on port 8001

## Quick Start

### 1. Start the Backend

```bash
cd backend
python api_server.py
```

The backend will run on `http://localhost:8001`

### 2. Enable Ngrok in Backend

Set the environment variable to enable ngrok CORS support:

```bash
export ENABLE_NGROK=true
```

Or add it to your `.env` file:
```
ENABLE_NGROK=true
```

### 3. Start Ngrok Tunnel

**Option A: Use the script**
```bash
./start_ngrok.sh
```

**Option B: Manual command**
```bash
ngrok http 8001
```

### 4. Get Your Public URL

After starting ngrok, you'll see output like:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8001
```

Use the `https://` URL as your public backend URL.

## Testing

1. **Health Check:**
   ```
   curl https://your-ngrok-url.ngrok-free.app/health
   ```

2. **Update Frontend:**
   If your frontend needs to connect, update the API URL to use the ngrok URL.

## Notes

- Free ngrok URLs change each time you restart ngrok
- For a static URL, upgrade to ngrok paid plan
- The backend CORS is configured to allow ngrok domains when `ENABLE_NGROK=true`
- Ngrok free tier has request limits

## Troubleshooting

- **CORS errors:** Make sure `ENABLE_NGROK=true` is set
- **Connection refused:** Ensure backend is running on port 8001
- **ngrok not found:** Install with `brew install ngrok`

