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

# ---------- 1️⃣ Open Source Calendar Tool ----------
def calendar_tool(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve holidays (from OpenHolidayAPI) and events (mock or open datasets)
    between start_date and end_date for a given location.
    """

    location = query.get("location", "US")
    start_date = query.get("start_date")
    end_date = query.get("end_date")
    event_types = query.get("event_types", ["holiday"])

    start_year = datetime.fromisoformat(start_date).year
    end_year = datetime.fromisoformat(end_date).year

    # --- Normalize country code ---
    country_codes = {
        "united states": "US",
        "usa": "US",
        "germany": "DE",
        "france": "FR",
        "italy": "IT",
        "spain": "ES",
        "canada": "CA",
        "india": "IN",
        "japan": "JP",
        "australia": "AU",
    }
    country_code = country_codes.get(location.lower(), "US")

    holidays: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    # ---------- Fetch OpenHolidayAPI holidays ----------
    if "holiday" in event_types:
        try:
            for year in range(start_year, end_year + 1):
                resp = requests.get(
                    f"https://openholidaysapi.org/PublicHolidays",
                    params={"countryIsoCode": country_code, "languageIsoCode": "EN", "validFrom": start_date, "validTo": end_date},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for h in data:
                        holidays.append({
                            "date": h.get("startDate"),
                            "name": h.get("name", {}).get("text", "Unknown Holiday"),
                            "type": h.get("type", "national").lower(),
                            "impact": "businesses_closed" if h.get("type") == "public" else "minor",
                        })
        except Exception as e:
            print(f"⚠️ Failed to fetch open holidays: {e}")

    # ---------- Sample open event dataset (mock/festival) ----------
    if any(et in ["festival", "cultural", "sporting", "concert"] for et in event_types):
        events = [
            {
                "date": "2025-11-07",
                "name": "Open Music Fest",
                "type": "concert",
                "description": "An open, free concert celebrating local artists in public parks.",
                "expected_crowds": "high",
                "ticket_required": False,
            },
            {
                "date": "2025-11-11",
                "name": "City Cultural Parade",
                "type": "cultural",
                "description": "Open cultural parade celebrating heritage and community art.",
                "expected_crowds": "moderate",
                "ticket_required": False,
            },
        ]

    return {
        "calendar_info": {
            "holidays": holidays,
            "events": events,
        }
    }


# ---------- 2️⃣ JSON Schema ----------
calendar_schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
        "event_types": {
            "type": "array",
            "items": {"type": "string", "enum": ["holiday", "festival", "cultural", "sporting", "concert"]},
        },
        "calendar_info": {
            "type": "object",
            "properties": {
                "holidays": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "impact": {"type": "string"},
                        },
                        "required": ["date", "name", "type", "impact"],
                    },
                },
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "expected_crowds": {"type": "string"},
                            "ticket_required": {"type": "boolean"},
                        },
                        "required": ["date", "name", "type", "description", "expected_crowds", "ticket_required"],
                    },
                },
            },
            "required": ["holidays", "events"],
        },
    },
    "required": ["location", "start_date", "end_date"],
}


# ---------- 3️⃣ Agent (Direct Execution, No Follow-Up) ----------
def calendar_agent(user_prompt: str) -> Dict[str, Any]:
    """
    Claude → CalendarTool → direct JSON output.
    """

    system_prompt = (
        "You are an open-source calendar assistant. "
        "Call the `calendar_tool` with location, start_date, end_date, and event_types, "
        "and return structured JSON according to the provided schema."
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "calendar_tool",
                "description": "Fetch open-source holidays and events for a given location and date range.",
                "input_schema": calendar_schema,
            }
        ],
        tool_choice={"type": "tool", "name": "calendar_tool"},
        max_tokens=1024,
    )

    if not response.content:
        print("⚠️ Empty response.")
        return {}

    first_block = response.content[0]
    if first_block.type != "tool_use":
        print("⚠️ No tool call detected.")
        return {}

    print("📅 CalendarTool invoked with:", first_block.input)
    result = calendar_tool(first_block.input)
    print("\n✅ Final JSON Output:\n", json.dumps(result, indent=2))
    return result


# ---------- 4️⃣ Example Run ----------
if __name__ == "__main__":
    user_prompt = (
        "Show open-source holidays and cultural events in Germany between 2025-11-05 and 2025-11-15."
    )
    calendar_agent(user_prompt)
