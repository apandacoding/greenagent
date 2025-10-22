import os
import requests
import anthropic
from typing import Dict, Any
from dotenv import load_dotenv
import json


load_dotenv()
YELP_API_KEY = '4MeBlkLJelePHyMrDynDZ1KyTrg0QnJ79bxdvPgxRJ4zOHN5BC0uok7UUei5_U_L6YDTsHJkJZYsL2VyXueyCIhpbY9HnvoYc27VZOdZ3VoYCYus6zfztCtsM1v5aHYx'
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)



def yelp_tool(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a Yelp API call based on structured input from Claude.
    Expected query fields: city, cuisine, price_level, open_now.
    """
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    base_url = "https://api.yelp.com/v3/businesses/search"

    price_map = {"$": "1", "$$": "2", "$$$": "3", "$$$$": "4"}
    params = {
        "term": query.get("cuisine", "restaurant"),
        "location": query.get("city", "San Francisco"),
        "categories": "restaurants",
        "price": price_map.get(query.get("price_level", "$$"), "2"),
        "limit": 5,
        "sort_by": "rating",
    }

    if query.get("open_now", True):
        params["open_now"] = "true"

    r = requests.get(base_url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    restaurants = []
    for biz in data.get("businesses", []):
        restaurants.append(
            {
                "name": biz.get("name"),
                "rating": biz.get("rating"),
                "price_level": biz.get("price", ""),
                "address": " ".join(biz["location"].get("display_address", [])),
                "city": biz["location"].get("city"),
                "phone": biz.get("display_phone"),
                "website": biz.get("url"),
                "highlights": [cat["title"] for cat in biz.get("categories", [])],
                "latitude": biz["coordinates"].get("latitude"),
                "longitude": biz["coordinates"].get("longitude"),
            }
        )

    return {"restaurants": restaurants}


# ---------- 2️⃣ Tool Schema ----------
yelp_schema = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "cuisine": {"type": "string"},
        "price_level": {"type": "string", "enum": ["$", "$$", "$$$", "$$$$"]},
        "open_now": {"type": "boolean"},
    },
    "required": ["city", "cuisine"],
}


# ---------- 3️⃣ Restaurant Agent (Claude ↔ YelpTool) ----------
def restaurant_agent(user_prompt: str) -> Dict[str, Any]:
    """
    Claude (White Agent) → YelpTool integration.
    Claude decides when/how to call YelpTool, and YelpTool executes the API call.
    """
    system_prompt = (
        "You are a restaurant search assistant that uses real Yelp data.\n"
        "When a user asks for dining options, call the `yelp_tool` with the right parameters.\n"
        "Extract the user's city, cuisine, price level ($–$$$$), and open_now flag.\n"
        "Return the Yelp results and summarize them helpfully for the user."
    )

    # First, let Claude interpret the user query and decide if it should call the YelpTool
    response = client.messages.create(
        model="claude-sonnet-4-5",
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "yelp_tool",
                "description": "Get real restaurants from the Yelp API given location and cuisine.",
                "input_schema": yelp_schema,
            }
        ],
        tool_choice={"type": "auto"},  # let Claude decide
        max_tokens=1024,
    )

    # If Claude decides to call the Yelp tool:
    content_block = response.content[0]

    if content_block.type == "tool_use":
        # ---- 1. Run Yelp API ----
        result = yelp_tool(content_block.input)
        print("🧭 YelpTool invoked with:", content_block.input)

        # ---- 2. Send results back to Claude (using correct tool_result format) ----

        followup = client.messages.create(
    model="claude-sonnet-4-5",
    system=system_prompt,
    messages=[
        {"role": "user", "content": user_prompt},
        {
            "role": "assistant",
            "content": [content_block],  # Claude's original tool call
        },
        {
            # ✅ Move tool_result into a "user" message, not "assistant"
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ],
                }
            ],
        },
    ],
    max_tokens=512,
)

        return result
