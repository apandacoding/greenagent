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
from tools.restaurant import restaurant_tool
from langchain.tools import BaseTool
from tools.hotels import hotel_tool

logger = logging.getLogger(__name__)

class FlightSearchTool(BaseTool):
    name: str = Field(
        default="flight_search", 
        description="Searches for flights between locations with dates, prices, airlines, and options."
    )
    description: str = Field(
        default=(
            "Searches and analyzes flights based on user context and query. "
            "Use this tool when the user wants to: book flights, search for flights, find flight options, "
            "compare flight prices, check flight availability, or plan air travel. "
            "This tool can extract departure/arrival locations, dates, and preferences from natural language. "
            "For itinerary planning, use this FIRST if flights are needed, then use other tools like restaurant_search "
            "for the destination. The tool returns detailed flight information including prices, times, airlines, and duration."
        ),
        description="Searches and analyzes flights based on user context and query."
    )
    context: List[Dict[str, str]] = Field(default_factory=list, description="The context of the conversation.")

    def set_context(self, context):
        self.context = context or []

    def clear_context(self):
        """Clear conversation context for new turn"""
        self.context = []

    def _run(self, query: str) -> str:
        try:
            print("✈️ Running FlightSearchTool:", query, flush=True)

            # Use ONLY the query - don't merge with context messages
            # The AgentExecutor already provides proper context through conversation history
            # Merging causes confusion (e.g., seeing both departure and return dates when agent only passes one)
            full_prompt = query.strip()
            
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


class RestaurantSearchTool(BaseTool):
    name: str = Field(
        default="restaurant_search", 
        description="Searches for restaurants, cafes, bars, and dining options at a specific location."
    )
    description: str = Field(
        default=(
            "Searches and analyzes restaurants, cafes, bars, and dining establishments based on user context and query. "
            "Use this tool when the user wants to: find restaurants, search for places to eat, look for cafes, "
            "find bars or nightlife, discover dining options, or get restaurant recommendations. "
            "This tool works best with a location (city, neighborhood, or address). "
            "For itinerary planning, use this AFTER flight_search if you know the destination city, "
            "or independently if the user just wants restaurant recommendations. "
            "The tool can filter by cuisine type, price range, ratings, and other preferences. "
            "It returns detailed information including names, ratings, prices, locations, and reviews."
        ),
        description="Searches and analyzes restaurants based on user context and query."
    )
    context: List[Dict[str, str]] = Field(default_factory=list, description="The context of the conversation.")

    def set_context(self, context):
        self.context = context or []

    def clear_context(self):
        """Clear conversation context for new turn"""
        self.context = []

    def _run(self, query: str) -> str:
        try:
            print("🍴 Running RestaurantSearchTool:", query, flush=True)

            # Use ONLY the query - don't merge with context messages
            # The AgentExecutor already provides proper context through conversation history
            # Merging causes confusion and double-processing
            full_prompt = query.strip()
            
            print("Full prompt:", full_prompt, flush=True)

            # 🔹 Call your real restaurant search
            result = restaurant_tool(full_prompt)
            print("Tool result preview:", (str(result)[:500] + "...") if result else "None", flush=True)
            return result or "No restaurants found."
        except Exception as e:
            print(f"[RestaurantSearchTool error] {e}", flush=True)
            return f"Error in RestaurantSearchTool: {e}"

    async def _arun(self, query: str):
        return await asyncio.to_thread(self._run, query)

class HotelSearchTool(BaseTool):
    name: str = Field(
        default="hotel_search", 
        description="Searches for hotels based on location and dates."
    )
    description: str = Field(
        default=(
            "Searches and analyzes hotels based on user context and query. "
            "Use this tool when the user wants to: find hotels, search for hotels, look for hotels, "
            "find the best hotels (reviews) and cost wise as well, discover hotel options, or get hotel recommendations. "
            "This tool works best with a location (city, neighborhood, or address). "
            "For itinerary planning, use this AFTER flight_search if you know the destination city, "
            "or independently if the user just wants hotel recommendations. "
            "The tool can filter by price range, ratings, and other preferences. "
            "It returns detailed information including names, ratings, prices, locations, and reviews."
        ),
        description="Searches and analyzes hotels based on user context and query."
    )
    context: List[Dict[str, str]] = Field(default_factory=list, description="The context of the conversation.")

    def set_context(self, context):
        self.context = context or []

    def clear_context(self):
        """Clear conversation context for new turn"""
        self.context = []

    def _run(self, query: str) -> str:
        try:
            print("🏨 Running HotelSearchTool:", query, flush=True)
            full_prompt = query.strip()
            print("Full prompt:", full_prompt, flush=True)
            result = hotel_tool(full_prompt)
            print("Tool result preview:", (str(result)[:500] + "...") if result else "None", flush=True)
            return result or "No hotels found."
        except Exception as e:
            print(f"[HotelSearchTool error] {e}", flush=True)
            return f"Error in HotelSearchTool: {e}"

    async def _arun(self, query: str):
        return await asyncio.to_thread(self._run, query)
