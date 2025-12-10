# Quick Start Guide - White Agent Chat

## ✅ All Import Issues Fixed!

The following fixes have been applied:
- ✅ Fixed `agent.py` to use relative imports
- ✅ Fixed `tools.py` to properly import from `tools.flights`
- ✅ Added `WhiteAgent` to package exports
- ✅ Test script confirms all imports work

## 🚀 How to Run

### Terminal 1 - Backend

```bash
cd /Users/aryanpanda/green-agent
source venv/bin/activate
cd backend
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloading process
INFO:     Application startup complete.
```

### Terminal 2 - Frontend

```bash
cd /Users/aryanpanda/green-agent/frontend
npm run dev
```

You should see:
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

## 🌐 Access the App

- **Green Agent (Full Demo)**: http://localhost:5173/
- **White Agent (Chat)**: http://localhost:5173/white-agent
- **API Docs**: http://localhost:8000/docs

## ✨ Test Backend Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy"
}
```

## 📝 Environment Variables

Make sure you have a `.env` file in `backend/chatbot/` with:

```env
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
SERP_API_KEY=your_key_here  
BASE_URL=https://serpapi.com/search
```

## 🧪 Test the Chat

1. Navigate to http://localhost:5173/white-agent
2. Type a message: "Looking for a flight from Oakland to Newark on 11/7/2025"
3. You should see the White Agent respond!

## 🐛 Troubleshooting

### Port Already in Use

**Backend:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Frontend:**
```bash
lsof -ti:5173 | xargs kill -9
```

### Import Errors

If you see import errors, make sure you're in the right directory:
- Backend must be run from `/Users/aryanpanda/green-agent/backend`
- Use the full uvicorn command as shown above

### ModuleNotFoundError

All imports have been fixed to use relative imports. If you still see errors:
1. Make sure venv is activated
2. Check that you're in the backend directory
3. Try `python test_imports.py` from the project root

## 📚 Files Changed

The following files were modified to fix imports:
- `backend/chatbot/agent.py` - Relative imports
- `backend/chatbot/tools.py` - Path handling
- `backend/chatbot/__init__.py` - Added WhiteAgent
- `backend/api_server.py` - Path setup

---

**All systems ready! 🎉**

