"""
Tools for the Green Agent chatbot, including flight booking functionality.
"""
import asyncio
import logging
from typing import Dict, Any, List
import sys
import os
import pandas as pd
from pydantic import Field
# import logger from lo
import logging

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from tools.flights import flight_tool
from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class FlightSearchTool(BaseTool):
    name: str = Field(default="flight_search", description="Searches and analyzes flights based on user context and query.")
    description: str = Field(default="Searches and analyzes flights based on user context and query.", description="Searches and analyzes flights based on user context and query.")
    context: List[Dict[str, str]] = Field(default_factory=list, description="The context of the conversation.")

    def set_context(self, context):
        self.context = context or []

    def clear_context(self):
        """Clear conversation context for new turn"""
        self.context = []

    def _run(self, query: str) -> str:
        try:
            print("✈️ Running FlightSearchTool:", query, flush=True)

            # Use only the current query, or combine with last user message if in same turn
            # Context should already be filtered to current turn by agent
            if self.context:
                # Get last user message from context (should be current turn only)
                user_messages = [m["content"] for m in self.context if m["role"] == "user"]
                if user_messages:
                    # Use the last user message + current query
                    full_prompt = f"{user_messages[-1]}\n\n{query}".strip()
                else:
                    full_prompt = query
            else:
                # No context (fresh turn) - use query only
                full_prompt = query
            
            print("Full prompt:", full_prompt, flush=True)

            # Try to extract params, but don't die if helper isn't present
            try:
                from tools.flights import get_flight_params
                params = get_flight_params(full_prompt)
                print("Parsed params:", params, flush=True)
            except Exception as e:
                print(f"[param-extract skipped] {e}", flush=True)

            # 🔹 Call your real flight search
            result = flight_tool(full_prompt)
            print("Tool result preview:", (str(result)[:500] + "...") if result else "None", flush=True)
            return result or "No flights found."
        except Exception as e:
            print(f"[FlightSearchTool error] {e}", flush=True)
            return f"Error in FlightSearchTool: {e}"

    async def _arun(self, query: str):
        return await asyncio.to_thread(self._run, query)
