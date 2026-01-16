"""Configuration management for RepoScraper."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment."""
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")  # Use gpt-5 when available
    
    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    
    # App
    APP_NAME: str = "RepoScraper"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
