from abc import ABC, abstractmethod
from typing import Optional


class BaseAIClient(ABC):
    """Base class for all AI clients"""

    @abstractmethod
    def send_prompt(
        self,
        system_prompt: str,
        instruction_prompt: str,
        output_structure_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4000
    ) -> str:
        """
        Send a prompt to the AI service and return the response.

        Args:
            system_prompt: The system message to set context
            instruction_prompt: The main instruction/question
            output_structure_prompt: Optional prompt to specify output format
            model: AI model to use (provider-specific)
            max_tokens: Maximum tokens in response

        Returns:
            String response from the AI service
        """
        pass