"""
Tools for the Green Agent chatbot, including flight booking functionality.
"""
import asyncio
import logging
from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import flights.py
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from flights import flight_tool, chat_node
import pandas as pd

logger = logging.getLogger(__name__)

class FlightTool:
    """Tool for handling flight-related requests"""
    
    def __init__(self):
        self.name = "flight_search"
        self.description = "Search for flights and provide booking information"
    
    async def execute(self, query: str) -> Dict[str, Any]:
        """Execute flight search based on user query"""
        try:
            logger.info(f"Executing flight search for query: {query}")
            
            # Use the flight_tool from flights.py
            flight_data = flight_tool(query)
            
            if flight_data is not None and not flight_data.empty:
                # Convert to dict for JSON serialization
                result = {
                    "status": "success",
                    "data": flight_data.to_dict('records'),
                    "total_flights": len(flight_data),
                    "message": f"Found {len(flight_data)} flight options"
                }
            else:
                result = {
                    "status": "no_results",
                    "data": [],
                    "total_flights": 0,
                    "message": "No flights found for your criteria"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in flight search: {e}")
            return {
                "status": "error",
                "data": [],
                "total_flights": 0,
                "message": f"Error searching for flights: {str(e)}"
            }

class AnalysisTool:
    """Tool for analyzing flight data and providing insights"""
    
    def __init__(self):
        self.name = "analysis"
        self.description = "Analyze flight data and provide insights"
    
    async def execute(self, query: str) -> Dict[str, Any]:
        """Execute analysis on flight data"""
        try:
            logger.info(f"Executing analysis for query: {query}")
            
            # This would typically analyze flight data
            # For now, return a simple analysis
            analysis_result = {
                "status": "success",
                "insights": [
                    "Best time to book: 2-3 weeks in advance",
                    "Consider flexible dates for better prices",
                    "Check multiple airlines for best deals"
                ],
                "recommendations": [
                    "Book during off-peak hours",
                    "Consider nearby airports",
                    "Sign up for price alerts"
                ]
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return {
                "status": "error",
                "insights": [],
                "recommendations": [],
                "message": f"Error in analysis: {str(e)}"
            }

class ChatAnalysisTool:
    """Tool for using PandasAI to analyze flight data"""
    
    def __init__(self):
        self.name = "chat_analysis"
        self.description = "Use natural language to analyze flight data"
    
    async def execute(self, query: str, flight_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Execute chat-based analysis on flight data"""
        try:
            if flight_data is None or flight_data.empty:
                return {
                    "status": "no_data",
                    "message": "No flight data available for analysis"
                }
            
            logger.info(f"Executing chat analysis for query: {query}")
            
            # Use the chat_node function from flights.py
            analysis_result = chat_node(flight_data, query)
            
            return {
                "status": "success",
                "analysis": analysis_result,
                "message": "Analysis completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in chat analysis: {e}")
            return {
                "status": "error",
                "analysis": None,
                "message": f"Error in analysis: {str(e)}"
            }
