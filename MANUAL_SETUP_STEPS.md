# Manual Setup - Step by Step

## Step 1: Kill Everything First

```bash
pkill -9 ngrok
pkill -f agentbeats_controller
pkill -f proxy_server
sleep 3
```

## Step 2: Start Green Agent Controller

**Terminal 1:**
```bash
cd /Users/aryanpanda/green-agent
source venv/bin/activate

ROLE=green AGENT_PORT=8001 HOST=0.0.0.0 \
python backend/agentbeats_controller.py --port 8101 --host 0.0.0.0
```

## Step 3: Start White Agent Controller

**Terminal 2:**
```bash
cd /Users/aryanpanda/green-agent
source venv/bin/activate

ROLE=white AGENT_PORT=8002 HOST=0.0.0.0 \
python backend/agentbeats_controller.py --port 8102 --host 0.0.0.0
```

## Step 4: Start Proxy Server

**Terminal 3:**
```bash
cd /Users/aryanpanda/green-agent
source venv/bin/activate

python proxy_server.py
```

## Step 5: Start ngrok

**Terminal 4:**
```bash
ngrok http 8100
```

Copy the ngrok URL from the output (e.g., `https://abc-xyz.ngrok-free.app`)

## Step 6: Test

```bash
# Replace with YOUR ngrok URL
curl https://YOUR-URL.ngrok-free.app/green/status
curl https://YOUR-URL.ngrok-free.app/white/status
```

## Step 7: Update Controllers with Public URL (Optional)

If you want the controllers to show the public URL, restart them with:

**Terminal 1 (restart green):**
```bash
ROLE=green AGENT_PORT=8001 HOST=0.0.0.0 \
python backend/agentbeats_controller.py --port 8101 --host 0.0.0.0 \
--public-url "https://YOUR-URL.ngrok-free.app/green"
```

**Terminal 2 (restart white):**
```bash
ROLE=white AGENT_PORT=8002 HOST=0.0.0.0 \
python backend/agentbeats_controller.py --port 8102 --host 0.0.0.0 \
--public-url "https://YOUR-URL.ngrok-free.app/white"
```


