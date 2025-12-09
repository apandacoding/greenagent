import requests
import anthropic
import json
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import os

# ---------- Setup ----------
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or "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"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
