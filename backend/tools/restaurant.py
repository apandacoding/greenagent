import os
import requests
import anthropic
from typing import Dict, Any
from dotenv import load_dotenv
import json
from langchain_core.runnables import RunnableLambda

# ---------- Load keys ----------
load_dotenv()
YELP_API_KEY = os.environ.get("YELP_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not YELP_API_KEY:
    raise ValueError("YELP_API_KEY environment variable is not set")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level from backend/tools/ to backend/, then into functions/
functions_dir = os.path.join(os.path.dirname(BASE_DIR), "functions")

with open(os.path.join(functions_dir, "yelp.json"), "r") as f:
    yelp_schema = json.load(f)

def get_yelp_info(original_prompt: str):
    """
    Extracts Yelp search parameters from a user's prompt using the Anthropic LLM with a tool-calling schema.
    """
    # Make sure yelp_schema is defined somewhere in your actual codebase before this call
    prompt_text = (
        f"User's complete original request: {original_prompt}\n\n"
        "CRITICAL: Determine the type of query from the user's request above.\n"
        "- General Restaurant and Business Information:\n"
    )

    

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[{
            "name": "get_business_info",
            "description": "ONLY use for identifying the parameters for the business information query.",
            "input_schema": yelp_schema,
        }],
        tool_choice={"type": "tool", "name": "get_business_info"},
        messages=[{"role": "user", "content": prompt_text}],
    )

    # Extract structured params
    if not response.content:
        raise ValueError("Empty response from Anthropic API when extracting Yelp params")

    first_block = response.content[0]

    if first_block.type != "tool_use":
        error_text = getattr(first_block, 'text', str(first_block))
        raise ValueError(f"Expected tool use but got {first_block.type}: {error_text}. The LLM did not call a Yelp params tool.")

    tool_name = getattr(first_block, 'name', 'unknown')
    print(f"🔧 LLM selected tool: {tool_name}", flush=True)

    params = dict(first_block.input)
    params['sort_by'] = 'best_match'
    params['limit'] = 5

    return {"params": params, "original_prompt": original_prompt}


def restaurant_tool(user_prompt: str):
    """
    Minimal-call pipeline:
      1. Extract Yelp parameters (1 LLM call)
      2. Call Yelp (1 REST call)
      3. Summarize result (1 LLM call)
    """
    # ---------- STEP 1: Extract params via Anthropic tool call ----------
    params_package = get_yelp_info(user_prompt)

    # ---------- STEP 2: Yelp API call ----------
    params = params_package["params"]
    prompt = params_package["original_prompt"]

    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    resp = requests.get(url, headers=headers, params=params)
    yelp_json = resp.json()

    if not yelp_json.get("businesses"):
        return "Sorry, no matching results were found."

    # ---------- STEP 3: Summarize with Anthropic ----------
    llm_prompt = (
        "You are an expert restaurant, travel, and nightlife assistant.\n\n"
        f"The user originally asked:\n\"{prompt}\"\n\n"
        "Below is the raw Yelp API response (unmodified), shown as JSON:\n\n"
        f"{json.dumps(yelp_json, indent=2)}\n\n"
        "Provide a concise, helpful answer."
    )

    llm_resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=900,
        messages=[{"role": "user", "content": llm_prompt}],
    )

    return llm_resp.content[0].text
