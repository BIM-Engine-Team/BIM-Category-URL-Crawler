import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv
from .base_client import BaseAIClient

load_dotenv()

class ClaudeClient(BaseAIClient):
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

    def send_prompt(
        self,
        system_prompt: str,
        instruction_prompt: str,
        output_structure_prompt: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 4000
    ) -> str:
        """
        Send a prompt to Claude and return the response.

        Args:
            system_prompt: The system message to set context
            instruction_prompt: The main instruction/question
            output_structure_prompt: Optional prompt to specify output format
            model: Claude model to use
            max_tokens: Maximum tokens in response

        Returns:
            String response from Claude
        """
        messages = [
            {"role": "user", "content": instruction_prompt}
        ]

        # Add output structure to the user message if provided
        if output_structure_prompt:
            messages[0]["content"] += f"\n\n{output_structure_prompt}"

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            # Log the error details if request fails
            if not response.ok:
                error_details = f"Status: {response.status_code}, Response: {response.text}"
                print(f"Claude API Error Details: {error_details}")
                print(f"Request payload: {json.dumps(payload, indent=2)}")

            response.raise_for_status()

            response_data = response.json()
            return response_data["content"][0]["text"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")


def send_claude_prompt(
    system_prompt: str,
    instruction_prompt: str,
    output_structure_prompt: Optional[str] = None,
    model: str = "claude-3-sonnet-20240229",
    max_tokens: int = 4000
) -> str:
    """
    Convenience function to send a prompt to Claude.

    Args:
        system_prompt: The system message to set context
        instruction_prompt: The main instruction/question
        output_structure_prompt: Optional prompt to specify output format
        model: Claude model to use
        max_tokens: Maximum tokens in response

    Returns:
        String response from Claude
    """
    client = ClaudeClient()
    return client.send_prompt(
        system_prompt=system_prompt,
        instruction_prompt=instruction_prompt,
        output_structure_prompt=output_structure_prompt,
        model=model,
        max_tokens=max_tokens
    )