# Hotel search tool using SerpAPI
import json
import os
import anthropic
from anthropic import InternalServerError, RateLimitError
import requests
import pandas as pd
from typing import Dict, Any, List
import dotenv
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_anthropic import ChatAnthropic
import logging

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
serp_api_key = os.getenv("SERP_API_KEY")

if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
if not serp_api_key:
    raise ValueError("SERP_API_KEY environment variable is not set")

BASE_URL = "https://serpapi.com/search"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level from backend/tools/ to backend/, then into functions/
functions_dir = os.path.join(os.path.dirname(BASE_DIR), "functions")

with open(os.path.join(functions_dir, "serp_params_hotels.json"), "r") as f:
    serp_params_hotels = json.load(f)


def sanitize_for_pandasai(df):
    """Sanitize DataFrame for PandasAI processing"""
    # Drop the pandas Index object entirely
    df = df.reset_index(drop=True).copy()

    # Convert datetimes to ISO strings
    for c in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[c] = df[c].astype(str)

    # Flatten lists / dicts
    for c in df.columns:
        df[c] = df[c].apply(lambda x: ", ".join(x) if isinstance(x, list)
                            else str(x) if isinstance(x, dict) or pd.isna(x)
                            else x)
    return df


def google_hotels_to_df(resp: Dict[str, Any]) -> pd.DataFrame:
    """
    Transform a SerpAPI `google_hotels` response dict into a flat pandas DataFrame.
    Focuses on the main property list (hotels / vacation rentals).
    """
    # SerpAPI usually puts hotels under 'properties'; fall back just in case
    properties: List[Dict[str, Any]] = (
        resp.get("properties")
        or resp.get("hotels")
        or resp.get("results")
        or []
    )

    rows = []
    for p in properties:
        gps = p.get("gps_coordinates", {}) or {}
        rate_per_night = p.get("rate_per_night", {}) or {}
        total_rate = p.get("total_rate", {}) or {}

        rows.append(
            {
                "type": p.get("type"),  # hotel / vacation rental / etc
                "name": p.get("name"),
                "description": p.get("description"),

                # Pricing
                "night_lowest": rate_per_night.get("extracted_lowest"),
                "night_lowest_str": rate_per_night.get("lowest"),
                "total_lowest": total_rate.get("extracted_lowest"),
                "total_lowest_str": total_rate.get("lowest"),

                # Class & ratings
                "hotel_class": p.get("extracted_hotel_class") or p.get("hotel_class"),
                "overall_rating": p.get("overall_rating"),
                "reviews": p.get("reviews"),

                # Location
                "lat": gps.get("latitude"),
                "lng": gps.get("longitude"),
                "location_rating": p.get("location_rating"),

                # Deal info
                "deal": p.get("deal"),
                "deal_description": p.get("deal_description"),

                # Link
                "link": p.get("link"),
                "serpapi_property_details_link": p.get("serpapi_property_details_link"),

                # Simplify amenities list into a CSV string
                "amenities": ", ".join(p.get("amenities", [])) if p.get("amenities") else None,
            }
        )

    return pd.DataFrame(rows)


def get_hotel_api_params(user_prompt: str):
    """Extract hotel search parameters using Anthropic API"""
    client = anthropic.Anthropic(api_key=anthropic_api_key)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        system="Return the hotel api params for the hotel search.",
        tools=[{
            "name": "get_hotel_api_params",
            "description": "Return the hotel api params for the hotel search",
            "input_schema": serp_params_hotels,
        }],
        tool_choice={"type": "tool", "name": "get_hotel_api_params"},
        messages=[{"role": "user", "content": f"User prompt: {user_prompt}"}],
        max_tokens=1024
    )

    if not response.content:
        raise ValueError("Empty response from Anthropic API")
    
    first_block = response.content[0]
    if first_block.type != "tool_use":
        error_text = first_block.text if hasattr(first_block, 'text') else str(first_block)
        raise ValueError(f"Expected tool use but got {first_block.type}: {error_text}")
    
    hotel_api_params = first_block.input 
    return hotel_api_params


def hotel_tool(user_prompt: str):
    """Main hotel search function"""
    try:
        # Get hotel API parameters
        params = get_hotel_api_params(user_prompt)
        params["api_key"] = serp_api_key
        print(params)
        url = "https://serpapi.com/search"
        
        logger.info(f"Making hotel search request with params: {params}")
        
        # Make API request
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        
    except requests.exceptions.HTTPError as e:
        # API returned error status (400, 404, etc.)
        status_code = response.status_code if hasattr(response, 'status_code') else 'unknown'
        error_detail = ""
        try:
            error_data = response.json()
            error_detail = error_data.get('error', '')
        except:
            error_detail = str(e)
        
        error_msg = (
            f"Error fetching hotels from API (status {status_code}). "
            f"API Error: {error_detail}. "
            f"Please provide complete hotel search information including location, check-in date, and check-out date."
        )
        logger.error(f"SerpAPI error: {status_code} - {error_detail}")
        logger.error(f"Params sent: {params}")
        return error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error connecting to hotel API: {str(e)}"
        logger.error(f"Hotel API network error: {e}")
        return error_msg

    # Check if response has valid hotel data
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        error_msg = f"Invalid response from hotel API: {str(e)}"
        logger.error(f"JSON decode error: {e}")
        return error_msg
    
    # Validate that we have hotel data
    properties = data.get("properties") or data.get("hotels") or data.get("results") or []
    if not properties:
        error_msg = (
            "No hotel data returned from API. "
            "This may indicate missing or invalid search parameters. "
            "Please ensure you have provided: location, check-in date, and check-out date."
        )
        logger.warning(f"No hotel data in response. Params: {params}")
        return error_msg

    # Process hotel data
    try:
        df = google_hotels_to_df(data)
        if df.empty:
            error_msg = "No hotels found matching your search criteria."
            logger.warning(f"Empty DataFrame from hotel data. Params: {params}")
            return error_msg
        
        return chat_node(sanitize_for_pandasai(df), user_prompt)
    except (KeyError, ValueError) as e:
        # Handle missing columns/data structure issues
        error_msg = (
            f"Error processing hotel data: {str(e)}. "
            "The API response may be missing required hotel information. "
            "Please try again with complete hotel search details (location, check-in date, check-out date)."
        )
        logger.error(f"Hotel data processing error: {e}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error processing hotels: {str(e)}"
        logger.error(f"Unexpected error in hotel_tool: {e}", exc_info=True)
        
        # Check if it's an API error that we should retry
        error_str = str(e)
        if "500" in error_str or "Internal server error" in error_str or "api_error" in error_str:
            error_msg = (
                f"Hotel search temporarily unavailable due to API service error. "
                f"Please try again in a moment. Error: {str(e)[:200]}"
            )
        
        return error_msg


def chat_node(df, prompt):
    """Analyze hotel data using PandasAI agent"""
    import time
    
    agent = create_pandas_dataframe_agent(
        llm=ChatAnthropic(model="claude-sonnet-4-5", api_key=anthropic_api_key),
        df=df,
        verbose=True,
        allow_dangerous_code=True,
    )

    # Retry logic for transient API errors
    max_retries = 3
    retry_delay = 1  # Start with 1 second
    
    for attempt in range(max_retries):
        try:
            response = agent.invoke(prompt)['output']
            break  # Success, exit retry loop
        except (InternalServerError, RateLimitError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Anthropic API error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                # Last attempt failed
                logger.error(f"Anthropic API error after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            # Non-retryable errors, raise immediately
            logger.error(f"Non-retryable error in chat_node: {e}")
            raise

    def to_json(df):
        return json.loads(df.to_json(orient="records"))

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    system_prompt = (
        "You are a strict JSON Analyzer and Data Analyzer. "
        "When you receive a piece of data and a user's query, you must analyze the data and describe meaningful insights, findings, and trends back to the user in natural language as a direct answer to their query."
        " Your response should help the user understand the data and answer their question clearly and thoroughly."
        " Do not return uninterpreted code, do not return a DataFrame object, do not respond with raw unprocessed JSON, and do not output summaries unless they directly answer the user's specific question."
        f" The user's query is: {prompt}"
    )

    if type(response) != str:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            system=system_prompt,
            messages=[{"role": "assistant", "content": json.dumps(to_json(response))}],
            max_tokens=1024
        )
        return response.content[0].text
    else:
        return response

