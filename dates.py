import requests
import anthropic
import json
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import os

# ---------- Setup ----------
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
