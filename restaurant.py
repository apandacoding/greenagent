import os
import requests
import anthropic
from typing import Dict, Any
from dotenv import load_dotenv
import json
import random

# ---------- Load keys ----------
load_dotenv()
YELP_API_KEY = '4MeBlkLJelePHyMrDynDZ1KyTrg0QnJ79bxdvPgxRJ4zOHN5BC0uok7UUei5_U_L6YDTsHJkJZYsL2VyXueyCIhpbY9HnvoYc27VZOdZ3VoYCYus6zfztCtsM1v5aHYx'
ANTHROPIC_API_KEY = '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'

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ---------- 1️⃣ Yelp Tool ----------
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
                "restaurant_id": biz.get("id"),
                "name": biz.get("name"),
                "address": " ".join(biz["location"].get("display_address", [])),
                "coordinates": {
                    "lat": biz["coordinates"].get("latitude"),
                    "lng": biz["coordinates"].get("longitude"),
                },
                "cuisine_type": query.get("cuisine", "Unknown"),
                "price_range": biz.get("price", "$$"),
                "rating": biz.get("rating", 0),
                "review_count": biz.get("review_count", 0),
                "availability": ["6:00 PM", "7:00 PM", "8:00 PM"],  # placeholder
                "dietary_options": ["vegetarian", "gluten-free"],
                "ambiance": random.choice(["casual", "romantic", "lively", "formal"]),
                "specialties": [cat["title"] for cat in biz.get("categories", [])],
                "average_meal_duration": random.choice([60, 75, 90]),
                "reservation_required": random.choice([True, False]),
            }
        )

    return {"restaurant_options": restaurants}


# ---------- 2️⃣ Input Schema ----------
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


# ---------- 3️⃣ Restaurant Agent ----------
def restaurant_search_tool(user_prompt: str) -> Dict[str, Any]:
    """
    Claude (White Agent) → YelpTool integration → JSON structured output.
    """
    system_prompt = (
        "You are a structured restaurant recommendation assistant using the Yelp API.\n"
        "When the user asks for dining options, always call the `yelp_tool` with correct parameters.\n"
        "Then, convert the Yelp API results into the following JSON schema exactly:\n\n"
        "**Outputs**:\n"
        "- restaurant_options (list): Array of dining options\n"
        "  - restaurant_id (string): Unique booking reference\n"
        "  - name (string): Restaurant name\n"
        "  - address (string): Full address\n"
        "  - coordinates (object): {lat: float, lng: float}\n"
        "  - cuisine_type (string): Primary cuisine\n"
        "  - price_range (string): \"$\" to \"$$$$\"\n"
        "  - rating (float): Average rating (1-5)\n"
        "  - review_count (int): Number of reviews\n"
        "  - availability (list): Available time slots\n"
        "  - dietary_options (list): Accommodations offered\n"
        "  - ambiance (string): \"casual\", \"romantic\", \"lively\", \"formal\"\n"
        "  - specialties (list): Signature dishes\n"
        "  - average_meal_duration (int): Minutes\n"
        "  - reservation_required (bool)\n\n"
        "Always respond with strictly valid JSON and nothing else."
    )

    # Step 1: Ask Claude to call the Yelp tool
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "yelp_tool",
                "description": "Get real restaurants from the Yelp API given location and cuisine.",
                "input_schema": yelp_schema,
            }
        ],
        tool_choice={"type": "tool", "name": "yelp_tool"},  # ✅ Force Yelp tool call
        max_tokens=1024,
    )

    if not response.content:
        print("⚠️ Empty response from Claude.")
        return {}

    first_block = response.content[0]
    if first_block.type != "tool_use":
        print("⚠️ Claude chose not to call YelpTool.")
        print(first_block.text)
        return {}

    # Step 2: Run Yelp API
    print("🧭 YelpTool invoked with:", first_block.input)
    result = yelp_tool(first_block.input)

    # Step 3: Send tool result and force JSON output
    followup = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": [first_block]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": first_block.id,
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2),
                            }
                        ],
                    }
                ],
            },
        ],
        max_tokens=1024,
    )

    # Step 4: Parse JSON output
    response_text = followup.content[0].text.strip()
    print("\n🤖 Claude JSON Output:")
    print(response_text)

    try:
        parsed_json = json.loads(response_text)
        return parsed_json
    except json.JSONDecodeError:
        print("⚠️ Warning: Claude returned non-JSON output. Returning raw text.")
        return {"raw_output": response_text}


# ---------- 4️⃣ Run Example ----------
if __name__ == "__main__":
    user_prompt = "Find me a romantic Italian restaurant in San Francisco open now"
    result = restaurant_agent(user_prompt)
    print("\nFinal JSON Output:\n", json.dumps(result, indent=2))
