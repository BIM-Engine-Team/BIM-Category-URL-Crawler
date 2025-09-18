import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient
from .google_client import GoogleClient
from .base_client import BaseAIClient

load_dotenv()


class AIMiddleware:
    """Middleware to route AI requests to different providers based on configuration"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._clients: Dict[str, BaseAIClient] = {}
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default config if file not found
            return {
                "ai_provider": "anthropic",
                "ai_model": "claude-3-sonnet-20240229"
            }
        except Exception as e:
            raise Exception(f"Failed to load config from {self.config_path}: {str(e)}")

    def _get_client(self, provider: str) -> BaseAIClient:
        """Get or create a client for the specified provider"""
        if provider not in self._clients:
            if provider == "anthropic":
                self._clients[provider] = ClaudeClient()
            elif provider == "openai":
                self._clients[provider] = OpenAIClient()
            elif provider == "google":
                self._clients[provider] = GoogleClient()
            else:
                raise ValueError(f"Unsupported AI provider: {provider}")

        return self._clients[provider]

    def send_prompt(
        self,
        system_prompt: str,
        instruction_prompt: str,
        output_structure_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4000
    ) -> str:
        """
        Send a prompt to an AI provider based on configuration.
        Fails immediately if the configured provider/model doesn't work.

        Args:
            system_prompt: The system message to set context
            instruction_prompt: The main instruction/question
            output_structure_prompt: Optional prompt to specify output format
            provider: AI provider to use ('anthropic', 'openai', 'google').
                     If None, uses provider from config
            model: Specific model to use. If None, uses model from config
            max_tokens: Maximum tokens in response

        Returns:
            String response from the AI service

        Raises:
            Exception: If the configured provider/model fails
        """
        # Use config values if not provided
        target_provider = provider or self._config.get("ai_provider", "anthropic")
        target_model = model or self._config.get("ai_model")

        # Get the client and send the request - no fallback, fail fast
        client = self._get_client(target_provider)
        return client.send_prompt(
            system_prompt=system_prompt,
            instruction_prompt=instruction_prompt,
            output_structure_prompt=output_structure_prompt,
            model=target_model,
            max_tokens=max_tokens
        )


# Global middleware instance
_middleware_instance = None

def get_ai_middleware() -> AIMiddleware:
    """Get the global AI middleware instance"""
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = AIMiddleware()
    return _middleware_instance


def send_ai_prompt(
    system_prompt: str,
    instruction_prompt: str,
    output_structure_prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4000
) -> str:
    """
    Convenience function to send a prompt to AI providers.
    This is the main function that other parts of the code should use.

    Args:
        system_prompt: The system message to set context
        instruction_prompt: The main instruction/question
        output_structure_prompt: Optional prompt to specify output format
        provider: AI provider to use ('anthropic', 'openai', 'google').
                 If None, uses provider from config
        model: Specific model to use. If None, uses model from config
        max_tokens: Maximum tokens in response

    Returns:
        String response from the AI service
    """
    middleware = get_ai_middleware()
    return middleware.send_prompt(
        system_prompt=system_prompt,
        instruction_prompt=instruction_prompt,
        output_structure_prompt=output_structure_prompt,
        provider=provider,
        model=model,
        max_tokens=max_tokens
    )