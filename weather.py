import os
import json
import requests
import anthropic
from typing import Dict, Any, List
from dotenv import load_dotenv
from datetime import datetime

# ---------- Setup ----------
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ---------- 1️⃣ Open-Source Weather Tool ----------
def weather_tool(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetches daily weather forecast or historical weather using Open-Meteo API.
    Automatically switches to archive API for past dates.
    """

    location = query.get("location", "San Francisco")
    start_date = query.get("start_date", datetime.now().strftime("%Y-%m-%d"))
    end_date = query.get("end_date", datetime.now().strftime("%Y-%m-%d"))

    # Convert to datetime objects
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Expected YYYY-MM-DD."}

    today = datetime.now()

 
    def geocode(place: str):
        g_url = "https://geocoding-api.open-meteo.com/v1/search"
        r = requests.get(g_url, params={"name": place, "count": 1, "language": "en", "format": "json"}, timeout=10)
        data = r.json()
        if data.get("results"):
            lat = data["results"][0]["latitude"]
            lon = data["results"][0]["longitude"]
            return lat, lon
        return None, None

    lat, lon = geocode(location)
    if not lat or not lon:
        return {"error": f"Could not geocode location: {location}"}

    # ---------- Endpoint Selection ----------
    if end_dt < today:
        base_url = "https://archive-api.open-meteo.com/v1/archive"
    else:
        base_url = "https://api.open-meteo.com/v1/forecast"

    # ---------- Weather API Call ----------
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "sunrise",
            "sunset",
            "windspeed_10m_max",
            "uv_index_max",
        ],
        "timezone": "auto",
        "model": "gfs",  # Global Forecast System (up to 16 days ahead)
    }

    r = requests.get(base_url, params=params, timeout=15)
    data = r.json()
    print(data)
    daily = data.get("daily", {})
    weather_forecast: List[Dict[str, Any]] = []

    for i, date in enumerate(daily.get("time", [])):
        weather_forecast.append(
            {
                "date": date,
                "temp_high": daily.get("temperature_2m_max", [None])[i],
                "temp_low": daily.get("temperature_2m_min", [None])[i],
                "conditions": "sunny" if daily.get("precipitation_sum", [0])[i] == 0 else "rainy",
                "precipitation_amount": daily.get("precipitation_sum", [0])[i],
                "humidity": None,
                "wind_speed": daily.get("windspeed_10m_max", [0])[i],
                "uv_index": daily.get("uv_index_max", [0])[i],
                "sunrise": daily.get("sunrise", [None])[i][-5:] if daily.get("sunrise") else None,
                "sunset": daily.get("sunset", [None])[i][-5:] if daily.get("sunset") else None,
                "hourly_forecast": None,
            }
        )

    if not weather_forecast:
        return {
            "weather_forecast": [],
            "historical_average": {},
            "alerts": [
                {
                    "type": "none",
                    "severity": "minor",
                    "description": "No forecast or historical data found for this date range.",
                }
            ],
        }

    # ---------- Historical Averages ----------
    avg_temp_high = sum(d["temp_high"] for d in weather_forecast if d["temp_high"]) / len(weather_forecast)
    avg_temp_low = sum(d["temp_low"] for d in weather_forecast if d["temp_low"]) / len(weather_forecast)
    avg_precip_days = sum(1 for d in weather_forecast if d["precipitation_amount"] > 0)

    historical_average = {
        "avg_temp_high": avg_temp_high,
        "avg_temp_low": avg_temp_low,
        "avg_precipitation_days": avg_precip_days,
        "typical_conditions": "partly cloudy",
    }

    # ---------- Alerts ----------
    alerts = []
    max_temp = max(d["temp_high"] or 0 for d in weather_forecast)
    if max_temp > 35:
        alerts.append(
            {
                "type": "heat",
                "severity": "moderate",
                "description": "High temperatures expected — stay hydrated.",
            }
        )

    return {
        "weather_forecast": weather_forecast,
        "historical_average": historical_average,
        "alerts": alerts,
    }


# ---------- 2️⃣ Schema ----------
weather_schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
    },
    "required": ["location", "start_date", "end_date"],
}



def weather_agent(user_prompt: str) -> Dict[str, Any]:
    system_prompt = (
        "You are a weather assistant that retrieves forecasts and historical data using open-source APIs. "
        "Always call the `weather_tool` with location, start_date, and end_date, and return JSON output."
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "weather_tool",
                "description": "Get open-source weather forecast and historical data using Open-Meteo.",
                "input_schema": weather_schema,
            }
        ],
        tool_choice={"type": "tool", "name": "weather_tool"},
        max_tokens=1024,
    )

    if not response.content:
        print("⚠️ Empty response.")
        return {}

    first_block = response.content[0]
    if first_block.type != "tool_use":
        print("⚠️ Claude did not call weather_tool.")
        return {}

    result = weather_tool(first_block.input)
    return result
