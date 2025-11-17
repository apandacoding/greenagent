import os
import requests
import anthropic
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import json


# ---------- Load API Key ----------
load_dotenv()
ANTHROPIC_API_KEY = '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'
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


maps_schema = {
    "type": "object",
    "properties": {
        "route_info": {
            "type": "object",
            "description": "Structured route and travel details",
            "properties": {
                "distance": {
                    "type": "number",
                    "description": "Total route distance in kilometers",
                },
                "duration": {
                    "type": "integer",
                    "description": "Estimated travel time in minutes",
                },
                "duration_in_traffic": {
                    "type": "integer",
                    "description": "Estimated travel time in traffic (minutes)",
                },
                "steps": {
                    "type": "array",
                    "description": "Turn-by-turn route instructions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "instruction": {
                                "type": "string",
                                "description": "Direction text for this step",
                            },
                            "distance": {
                                "type": "number",
                                "description": "Step distance in kilometers",
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Step duration in minutes",
                            },
                        },
                        "required": ["instruction", "distance", "duration"],
                    },
                },
                "polyline": {
                    "type": "string",
                    "description": "Encoded route path for map display",
                },
                "traffic_conditions": {
                    "type": "string",
                    "enum": ["light", "moderate", "heavy"],
                    "description": "Qualitative estimate of route traffic",
                },
            },
            "required": [
                "distance",
                "duration",
                "steps",
                "polyline",
                "traffic_conditions",
            ],
        },
    },
    "required": ["route_info"],
}



# ---------- 3️⃣ Maps Agent (Claude ↔ OSRM) ----------
def maps_tool(user_prompt: str) -> Dict[str, Any]:
    """
    Claude (White Agent) → OSRM Tool → Enforced JSON output.
    """

    system_prompt = (
        "You are a navigation assistant that uses real OpenStreetMap (OSRM) data for directions.\n"
        "Always call the `maps_tool` with the correct structured parameters.\n\n"
    )

    # Step 1: Ask Claude to call the tool
    response = client.messages.create(
        model="claude-sonnet-4-5",
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "maps_tool",
                "description": "Get route, distance, and travel time using OpenStreetMap OSRM.",
                "input_schema": maps_schema,
            }
        ],
        tool_choice={"type": "tool", "name": "maps_tool"}, 
        max_tokens=1024,
    )

    return response.content[0].input
