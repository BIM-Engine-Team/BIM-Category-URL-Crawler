import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv
from .base_client import BaseAIClient

load_dotenv()

class OpenAIClient(BaseAIClient):
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def send_prompt(
        self,
        system_prompt: str,
        instruction_prompt: str,
        output_structure_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4000
    ) -> str:
        """
        Send a prompt to OpenAI and return the response.

        Args:
            system_prompt: The system message to set context
            instruction_prompt: The main instruction/question
            output_structure_prompt: Optional prompt to specify output format
            model: OpenAI model to use (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens in response

        Returns:
            String response from OpenAI
        """
        if model is None:
            model = "gpt-3.5-turbo"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction_prompt}
        ]

        if output_structure_prompt:
            messages.append({"role": "user", "content": output_structure_prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")