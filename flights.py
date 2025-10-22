# import json for flight_param
import json
import os
import anthropic
from jsonschema import validate, ValidationError
import requests
import time
import requests
import pandas as pd
from langchain_core.runnables import RunnableLambda, RunnableSequence
import dotenv
from pandasai.llm import OpenAI
from pandasai import SmartDataframe

dotenv.load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
serp_api_key = os.getenv("SERP_API_KEY")
BASE_URL = os.getenv("BASE_URL")


with open('./functions/serp_params_one_way.json', 'r') as f:
    serp_params_round_trip = json.load(f)

with open('./functions/serp_params_one_way.json', 'r') as f:
    serp_params_one_way = json.load(f)


iata_schema = {
    "type": "object",
    "properties": {
        "from": {"type": "string", "description": "The city of the departure", "pattern": "^[A-Z]{3}$"},
        "destination": {"type": "string", "description": "The city of the destination", "pattern": "^[A-Z]{3}$"},
        "original_prompt": {"type": "string", "description": "The original prompt from the user"}
    }
}

def transform_df(df):
    df = df.copy()

    # ensure datetimes
    df["depart_time"] = pd.to_datetime(df["depart_time"])
    df["arrive_time"] = pd.to_datetime(df["arrive_time"])

    # split
    out = df[df["direction"] == "outbound"].copy()
    ret = df[df["direction"] == "return"].copy()

    # keep only columns we need and rename to _out / _ret (keep airline/price for join)
    out = out.rename(columns={
        "from": "from_out",
        "to": "to_out",
        "depart_time": "depart_time_out",
        "arrive_time": "arrive_time_out",
        "duration_min": "duration_min_out",
        "layovers": "layovers_out",
        "price": "price_out",
    })
    ret = ret.rename(columns={
        "from": "from_ret",
        "to": "to_ret",
        "depart_time": "depart_time_ret",
        "arrive_time": "arrive_time_ret",
        "duration_min": "duration_min_ret",
        "layovers": "layovers_ret",
        "price": "price_ret",
    })

    # enforce pairing rule: same outbound_idx AND same airline AND same price
    # if multiple returns satisfy this, pick earliest return depart; tie-break shorter duration
    ret_sorted = ret.sort_values(["outbound_idx", "airline", "price_ret", "depart_time_ret", "duration_min_ret"])
    best_ret = (
        ret_sorted.groupby(["outbound_idx", "airline", "price_ret"], as_index=False)
                .first()
    )

    # join outbound to best matching return
    pairs = out.merge(
        best_ret,
        left_on=["outbound_idx", "airline", "price_out"],
        right_on=["outbound_idx", "airline", "price_ret"],
        how="inner",
    )

    # compute total price (robust even if prices differ in edge cases)
    pairs["total_price"] = pairs["price_out"]  # (or pairs["price_ret"])

    
    pairs.insert(0, "pair_id", range(1, len(pairs) + 1))

    
    df = pairs[[
        "pair_id",
        "total_price",
        "airline",
        "from_out", "to_out",
        "depart_time_out", "arrive_time_out", "duration_min_out", "layovers_out",
        "from_ret", "to_ret",
        "depart_time_ret", "arrive_time_ret", "duration_min_ret", "layovers_ret",
        "outbound_idx",
    ]].sort_values(["depart_time_out", "pair_id"]).reset_index(drop=True)

    return df


def flatten_direction(flights, direction, outbound_idx=None, outbound_airline=None):
    rows = []
    for f in flights:
        first, last = f["flights"][0], f["flights"][-1]
        rows.append({
            "direction": direction,
            "price": f.get("price"),
            "airline": f["flights"][0]["airline"],
            "from": first["departure_airport"]["id"],
            "to": last["arrival_airport"]["id"],
            "depart_time": first["departure_airport"]["time"],
            "arrive_time": last["arrival_airport"]["time"],
            "duration_min": f.get("total_duration"),
            "layovers": [l["id"] for l in f.get("layovers", [])],
            "carbon_kg": (f.get("carbon_emissions", {}).get("this_flight") or 0) // 1000,
            "token": f.get("departure_token"),
            "outbound_idx": outbound_idx,
            "paired_outbound_airline": outbound_airline,
        })
    return rows



def sanitize_for_pandasai(df):
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




def _get_all_outbounds(data):
    """Return a flat list of all outbound ‘flight bundles’ with departure_token from both sections."""
    all_outbounds = []
    for section_key in ("best_flights", "other_flights"):
        for f in data.get(section_key, []) or []:
            all_outbounds.append(f)
    return all_outbounds

def data_to_df(data, params):
    # ---------- 1) collect ALL outbounds & flatten them ----------
    outbound_flights = _get_all_outbounds(data)
    outbound_rows = []
    for i, f in enumerate(outbound_flights):
        outbound_rows += flatten_direction([f], "outbound", outbound_idx=i, outbound_airline=f["flights"][0]["airline"])

    return_rows = []
    for i, f in enumerate(outbound_flights):
        token = f.get("departure_token")
        if not token:
            continue  # some entries might not have a token

        # Build params fresh each time; don't mutate a shared dict
        params["departure_token"] = token
        params["api_key"] = serp_api_key
        
        r = requests.get(BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            print(f"⚠️ Failed return fetch for outbound #{i} ({r.status_code})")
            continue

        jr = r.json()

        # SerpAPI can place the return options in various buckets; try them in order.
        ret_list = (
            jr.get("return_flights")
            or jr.get("best_flights")
            or jr.get("other_flights")
            or []
        )

        # Flatten as "return" and keep the linkage to the originating outbound
        return_rows += flatten_direction(
            ret_list, "return", outbound_idx=i, outbound_airline=f["flights"][0]["airline"]
        )

        time.sleep(1)  # polite rate limiting

    # ---------- 3) combine, de-dupe, and sort ----------
    df = pd.DataFrame(outbound_rows + return_rows)
    if not df.empty:
        dedupe_cols = ["direction", "from", "to", "depart_time", "arrive_time", "airline", "price"]
        df = (
            df.drop_duplicates(subset=dedupe_cols)
              .sort_values(["direction", "outbound_idx", "depart_time"])
              .reset_index(drop=True)
        )
    
    return transform_df(df)


def anthropic_IATA_call(iata_result: str):
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    response = client.messages.create(
        model="claude-sonnet-4-5",
        system="Return the IATA codes for the city provided by the user",
        tools=[{
            "name": "get_iata_codes",
            "description": "Return the IATA codes for the city provided by the user",
            "input_schema": iata_schema,
        }],
        tool_choice={"type": "tool", "name": "get_iata_codes"},
        messages=[{"role": "user", "content": f"Cities mapped: {iata_result}"}], 
        max_tokens=1024
    )
    iata_codes = response.content[0].input 
    return iata_codes

def get_flight_api_params(iata_result: dict):
    client = anthropic.Anthropic(api_key=anthropic_api_key)

    # build a new structured prompt using the IATA result
    prompt_text = (
        f"User Original Request: {iata_result.get('original_prompt')}"
        f"Departure: {iata_result.get('from')} | "
        f"Arrival: {iata_result.get('destination')} | "
        f"Original user request included these IATA codes."
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[{
            "name": "get_flight_api_params_round_trip",
            "description": "Follow the tool call schema to fill out the api params for google flights for round trip flights (if user asks for round trip flights or mentions a return date)",
            "input_schema": serp_params_round_trip,
        },
        {
            "name": "get_flight_api_params_one_way",
            "description": "Follow the tool call schema to fill out the api params for google flights for one way flights",
            "input_schema": serp_params_one_way,
        },
        ],
        tool_choice={"type": "tool", "name": "get_flight_api_params_round_trip"},
        messages=[{"role": "user", "content": prompt_text}],
    )

    # Extract structured params
    tool_block = response.content[0]
    params = tool_block.input  # final Google Flights params dict
    params['api_key'] = '4a871fe30bb1fed4dc0850f01d384a2fff2dee8a74046b902109785f1a9bd730'

    return params

def get_flight_params(user_prompt: str):
    iata_chain = RunnableLambda(anthropic_IATA_call)
    flight_chain = RunnableLambda(get_flight_api_params)
    pipeline = iata_chain | flight_chain
    result = pipeline.invoke(user_prompt)
    return result


def flight_tool(user_prompt: str):
    iata_chain = RunnableLambda(anthropic_IATA_call)
    flight_chain = RunnableLambda(get_flight_api_params)
    pipeline = iata_chain | flight_chain
    result = pipeline.invoke(user_prompt)

    # make a flight booking
    params = result
    params['api_key'] = serp_api_key
    url = "https://serpapi.com/search"
    response = requests.get(url, params=params)
    data = response.json()
    return sanitize_for_pandasai(data_to_df(data, params))



def chat_node(df, prompt):
    
    llm = OpenAI(api_token="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", model="gpt-4")

    # Wrap your DataFrame
    sdf = SmartDataframe(df, config={"llm": llm})

    # Ask natural language questions
    response = sdf.chat(prompt)
    return response


if __name__ == "__main__":
    user_prompt = "Book me a round trip flight from Oakland to Newark on outbound_date of 11/7/2025 this year returning on 11/14/2025"
    data = flight_tool(user_prompt)
    print(data)
    response = chat_node(data, "What is the total price of the flight?")
    print(response)