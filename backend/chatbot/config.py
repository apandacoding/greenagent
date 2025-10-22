"""
Configuration settings for the Green Agent chatbot.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    serp_api_key: str = os.getenv("SERP_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Base URLs
    base_url: str = os.getenv("BASE_URL", "https://serpapi.com/search")
    
    # Model configurations
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4"
    
    # Agent settings
    max_conversation_length: int = 50
    response_timeout: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
