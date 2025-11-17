"""
Configuration settings for the Green Agent chatbot.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file from the chatbot directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    serp_api_key: str = os.getenv("SERP_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
   
    base_url: str = os.getenv("BASE_URL", "https://serpapi.com/search")
    
    
    anthropic_model: str = "claude-sonnet-4-5"
    openai_model: str = "gpt-5-nano"
    
    
    max_conversation_length: int = 50
    response_timeout: int = 30
    
    
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
