# 📋 How to Check Backend Logs

## Current Status

The backend is running with PID: 46854

## Method 1: View Live Logs (Recommended)

Since the backend was started in the background, restart it in the foreground to see live logs:

```bash
# Kill current backend
killall -9 uvicorn

# Start with visible logs
cd /Users/aryanpanda/green-agent
source venv/bin/activate
cd backend
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload
```

Now you'll see all logs in real-time in your terminal!

## Method 2: Log to a File

Start the backend and save logs to a file:

```bash
# Kill current backend
killall -9 uvicorn

# Start and log to file
cd /Users/aryanpanda/green-agent
source venv/bin/activate
cd backend
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload > backend.log 2>&1 &

# Watch logs in real-time
tail -f backend.log
```

To stop watching: Press `Ctrl+C`

## Method 3: Check Specific Log Levels

Add custom logging to see more details:

```bash
# With debug logging
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload --log-level debug

# Or info level (default)
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload --log-level info
```

## Method 4: Quick Status Check

```bash
# Health check
curl http://localhost:8001/health

# Check if process is running
ps aux | grep uvicorn

# Check what's on port 8001
lsof -i:8001
```

## What You'll See in Logs

### Startup Logs:
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
WARNING:  chatbot.agent:OpenAI API key not set - using Anthropic LLM only
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Request Logs:
```
INFO:     127.0.0.1:52104 - "GET /health HTTP/1.1" 200 OK
INFO:     Received message: Looking for a flight...
Processing user input
White Agent reasoning
INFO:     127.0.0.1:52104 - "POST /api/chat HTTP/1.1" 200 OK
```

### Error Logs:
```
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  ...
```

## Useful Commands

### Follow logs in real-time:
```bash
tail -f backend/backend.log
```

### Search logs for errors:
```bash
grep -i error backend/backend.log
```

### Search for specific messages:
```bash
grep "Received message" backend/backend.log
```

### Last 50 lines:
```bash
tail -n 50 backend/backend.log
```

### Clear old logs and restart:
```bash
rm backend/backend.log
cd /Users/aryanpanda/green-agent && source venv/bin/activate && cd backend
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload > backend.log 2>&1 &
tail -f backend.log
```

## Pro Tips

1. **Use `--reload`** - Auto-restarts on code changes (already enabled)
2. **Use `--log-level debug`** - See detailed information
3. **Pipe to file** - `> backend.log 2>&1` saves both stdout and stderr
4. **Use `tail -f`** - Follows logs as they're written
5. **Check health endpoint** - Quick way to verify server is responsive

## Current Recommended Setup

For development, run in foreground:
```bash
cd /Users/aryanpanda/green-agent && source venv/bin/activate && cd backend
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload --log-level info
```

This gives you:
- ✅ Real-time logs in your terminal
- ✅ Auto-reload on code changes
- ✅ Easy to stop with Ctrl+C
- ✅ Color-coded log levels
- ✅ Request/response logging

---

**Quick Reference:**
- Backend health: `curl http://localhost:8001/health`
- API docs: http://localhost:8001/docs
- Kill backend: `killall -9 uvicorn`







