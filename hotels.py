import os
import anthropic
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# --- Define the HotelTool ---

def hotel_booking_tool(user_prompt: str) -> Dict[str, Any]:
    """
    Call Claude to simulate a hotel search tool call.
    Extracts structured data (city, dates, guests, budget, etc.)
    and returns a JSON object describing a suitable hotel.
    """

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    # 1️⃣ Define the system instructions
    system_prompt = (
        "You are the HotelTool, a structured data generator for hotel booking tasks.\n"
        "When a user asks for lodging, you must call the `get_hotels` tool below.\n"
        "Extract: city, check-in/check-out dates, guests, budget, and pet-friendliness.\n"
        "Return realistic hotel data with JSON fields matching the schema.\n"
        "If dates aren't specified, infer check-in as 7 days from today and check-out 3 days later.\n"
        "All prices must be in USD."
    )

    # 2️⃣ Define the schema for tool-calling
    hotel_schema = {
        "type": "object",
        "properties": {
            "property_name": {"type": "string"},
            "rating": {"type": "number"},
            "price_per_night": {"type": "integer"},
            "total_price": {"type": "integer"},
            "currency": {"type": "string", "enum": ["USD"]},
            "location": {"type": "string"},
            "cancellation_policy": {"type": "string"},
            "amenities": {"type": "array", "items": {"type": "string"}},
            "pet_friendly": {"type": "boolean"},
            "check_in": {"type": "string", "format": "date"},
            "check_out": {"type": "string", "format": "date"},
            "city": {"type": "string"}
        },
        "required": [
            "property_name",
            "rating",
            "price_per_night",
            "total_price",
            "currency",
            "location",
            "cancellation_policy",
            "amenities",
            "pet_friendly",
            "check_in",
            "check_out",
            "city"
        ],
    }

    # 3️⃣ Call Claude with tool invocation
    response = client.messages.create(
        model="claude-sonnet-4-5",
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        tools=[
            {
                "name": "get_hotels",
                "description": "Return hotel booking details as structured JSON.",
                "input_schema": hotel_schema,
            }
        ],
        tool_choice={"type": "tool", "name": "get_hotels"},
        max_tokens=1024,
    )

    # 4️⃣ Parse structured tool call output
    tool_block = response.content[0]
    hotel_data = tool_block.input  # <-- structured JSON output

    return hotel_data


# --- Example usage ---
if __name__ == "__main__":
    user_prompt = "Find me a pet-friendly hotel in New York City from November 10th to November 13th for 2 guests under $200/night."
    result = hotel_booking_tool(user_prompt)
    print("\n🧳 Hotel search result:\n")
    print(result)
