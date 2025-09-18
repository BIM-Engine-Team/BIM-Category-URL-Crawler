import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv
from .base_client import BaseAIClient

load_dotenv()

class GoogleClient(BaseAIClient):
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.headers = {
            "Content-Type": "application/json"
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
        Send a prompt to Google Gemini and return the response.

        Args:
            system_prompt: The system message to set context
            instruction_prompt: The main instruction/question
            output_structure_prompt: Optional prompt to specify output format
            model: Google model to use (default: gemini-pro)
            max_tokens: Maximum tokens in response

        Returns:
            String response from Google Gemini
        """
        if model is None:
            model = "gemini-pro"

        # Combine all prompts for Google Gemini format
        combined_prompt = f"System: {system_prompt}\n\nUser: {instruction_prompt}"
        if output_structure_prompt:
            combined_prompt += f"\n\n{output_structure_prompt}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": combined_prompt
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            response_data = response.json()
            return response_data["candidates"][0]["content"]["parts"][0]["text"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")