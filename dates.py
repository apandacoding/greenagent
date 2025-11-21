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
