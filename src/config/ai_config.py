import os
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AIConfig(BaseModel):
    api_key: str = os.getenv('CLAUDE_API_KEY', '')
    model: str = 'claude-sonnet-4-20250514'
    max_tokens: int = 4000
    temperature: float = 0.1

    # Rate limiting
    requests_per_minute: int = 50
    requests_per_day: int = 1000

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # Cache settings
    cache_responses: bool = True
    cache_ttl: int = 3600  # seconds

    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
        return True