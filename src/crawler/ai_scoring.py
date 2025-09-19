"""
AI scoring functionality for web crawler.
Handles all AI interactions for scoring links and detecting product pages.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from .models import LinkInfo
from .utils import extract_page_content

# Try to import AI middleware, but make it optional for testing
try:
    from src.util.ai_client.ai_middleware import send_ai_prompt
except ImportError:
    try:
        from util.ai_client.ai_middleware import send_ai_prompt
    except ImportError:
        # Fallback for testing - mock AI response
        def send_ai_prompt(system_prompt, instruction_prompt, output_structure_prompt=None, max_tokens=4000):
            return '[]'  # Empty JSON array for testing


class AIScoring:
    """Handles AI-powered scoring of links and product page detection."""

    def __init__(self, system_prompt: str, ai_provider: str = None, ai_model: str = None):
        """
        Initialize AI scoring component.

        Args:
            system_prompt: Base system prompt for AI
            ai_provider: AI provider to use
            ai_model: AI model to use
        """
        self.system_prompt = system_prompt
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self.logger = logging.getLogger(__name__)

    def build_instruction_prompt(self, children_info: List[LinkInfo]) -> str:
        """Build the instruction prompt for AI scoring."""
        children_data = []
        for link_info in children_info:
            children_data.append({
                "id": link_info.id,
                "relative_path": link_info.relative_path,
                "title": link_info.title,
                "description": link_info.description
            })

        prompt = f"""You come to a page with a list of links. Here is the ID, relative path, title and description of each link.
Score them from 0 - 10 according to how likely the link will lead you to the product description page.
A score less than 1 is for links you will never click.
A score higher than 9 is for links you think is very likely to be the product description page of a specific product. For these kind of link, you will also tell the product name.

Links to analyze:
{json.dumps(children_data, indent=2)}"""

        return prompt

    def build_output_structure_prompt(self) -> str:
        """Build the output structure prompt for AI response."""
        return """Please format your response as JSON with the following structure:
[
    {"id": 0, "score": 3.4},
    {"id": 1, "score": 7.8},
    {"id": 2, "score": 9.5, "productName": "Emerald Urethane Trim Enamel"},
    ...
]

IMPORTANT:
- Include the 'id' field for each item to match it with the corresponding link
- Provide exactly one score object for each link
- Include 'productName' only when score > 9.0"""

    def get_ai_scores_with_retry(self, children_info: List[LinkInfo], max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Get AI scores with retry logic for invalid responses.

        Args:
            children_info: List of link information to score
            max_retries: Maximum number of retry attempts

        Returns:
            List of score dictionaries with proper ID-based matching
        """
        instruction_prompt = self.build_instruction_prompt(children_info)
        output_structure_prompt = self.build_output_structure_prompt()
        expected_count = len(children_info)

        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"[AI_RETRY] Attempt {attempt + 1}/{max_retries + 1} to get AI scores")

                # Get AI response
                ai_response = send_ai_prompt(
                    system_prompt=self.system_prompt,
                    instruction_prompt=instruction_prompt,
                    output_structure_prompt=output_structure_prompt,
                    provider=self.ai_provider,
                    model=self.ai_model,
                    max_tokens=4000
                )

                self.logger.debug(f"[AI_RETRY] Raw AI response (attempt {attempt + 1}): {ai_response}")

                # Try to parse the response
                parsed_scores = self._parse_ai_response(ai_response, expected_count)

                # Validate the parsed response
                if self._validate_ai_scores(parsed_scores, expected_count):
                    self.logger.info(f"[AI_RETRY] Successfully got valid AI scores on attempt {attempt + 1}")
                    return parsed_scores
                else:
                    self.logger.warning(f"[AI_RETRY] Invalid AI scores on attempt {attempt + 1}, will retry")
                    if attempt < max_retries:
                        continue

            except Exception as e:
                self.logger.error(f"[AI_RETRY] Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    continue

        # All retries failed, return default scores
        self.logger.error(f"[AI_RETRY] All {max_retries + 1} attempts failed, returning default scores")
        return [{"id": i, "score": 0.0} for i in range(expected_count)]

    def _validate_ai_scores(self, scores: List[Dict[str, Any]], expected_count: int) -> bool:
        """
        Validate AI scores response.

        Args:
            scores: List of score dictionaries to validate
            expected_count: Expected number of scores

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(scores, list):
            self.logger.error(f"[AI_VALIDATION] Expected list, got {type(scores)}")
            return False

        if len(scores) != expected_count:
            self.logger.error(f"[AI_VALIDATION] Expected {expected_count} scores, got {len(scores)}")
            return False

        # Check each score object
        for i, score_data in enumerate(scores):
            if not isinstance(score_data, dict):
                self.logger.error(f"[AI_VALIDATION] Score {i} is not a dictionary: {score_data}")
                return False

            if "score" not in score_data:
                self.logger.error(f"[AI_VALIDATION] Score {i} missing 'score' field: {score_data}")
                return False

            if not isinstance(score_data["score"], (int, float)):
                self.logger.error(f"[AI_VALIDATION] Score {i} has invalid score type: {score_data['score']}")
                return False

            # Validate ID field if present
            if "id" in score_data and not isinstance(score_data["id"], int):
                self.logger.error(f"[AI_VALIDATION] Score {i} has invalid id type: {score_data['id']}")
                return False

        self.logger.debug(f"[AI_VALIDATION] All {len(scores)} scores are valid")
        return True

    def _parse_ai_response(self, ai_response: str, expected_count: int) -> List[Dict[str, Any]]:
        """
        Parse AI response into list of score dictionaries with ID-based matching.

        Args:
            ai_response: Raw AI response string
            expected_count: Expected number of score objects

        Returns:
            List of score dictionaries sorted by ID
        """
        self.logger.debug(f"[AI_PARSING] Attempting to parse AI response for {expected_count} links")

        try:
            # Try to find JSON in the response
            start_idx = ai_response.find('[')
            end_idx = ai_response.rfind(']') + 1

            if start_idx == -1 or end_idx == 0:
                self.logger.error(f"[AI_PARSING] No JSON array found in response")
                raise ValueError("No JSON array found in response")

            json_str = ai_response[start_idx:end_idx]
            self.logger.debug(f"[AI_PARSING] Extracted JSON string: {json_str}")

            scores = json.loads(json_str)

            if not isinstance(scores, list):
                self.logger.error(f"[AI_PARSING] Expected JSON array, got {type(scores)}")
                raise ValueError("Expected JSON array")

            # Create ID-based mapping for proper matching
            id_to_score = {}
            for score_data in scores:
                if not isinstance(score_data, dict):
                    continue

                score_id = score_data.get("id")
                if score_id is not None and isinstance(score_id, int):
                    id_to_score[score_id] = score_data
                    self.logger.debug(f"[AI_PARSING] Mapped ID {score_id} to score {score_data.get('score', 'N/A')}")

            # Build ordered result based on expected IDs
            ordered_scores = []
            for i in range(expected_count):
                if i in id_to_score:
                    ordered_scores.append(id_to_score[i])
                else:
                    # Missing score for this ID, use default
                    default_score = {"id": i, "score": 0.0}
                    ordered_scores.append(default_score)
                    self.logger.warning(f"[AI_PARSING] Missing score for ID {i}, using default")

            self.logger.info(f"[AI_PARSING] Successfully parsed and ordered {len(ordered_scores)} scores")
            for i, score_data in enumerate(ordered_scores):
                score = score_data.get("score", 0.0)
                product_name = score_data.get("productName")
                self.logger.debug(f"[AI_PARSING] ID {i}: score {score}" + (f", product: {product_name}" if product_name else ""))

            return ordered_scores

        except Exception as e:
            self.logger.error(f"[AI_PARSING] Error parsing AI response: {e}")
            self.logger.debug(f"[AI_PARSING] Failed AI response was: {ai_response}")
            raise  # Re-raise to trigger retry logic

    def check_if_product_page_with_ai(self, url: str, session) -> Optional[str]:
        """
        Extract page content and use AI to determine if it's a product page.

        Args:
            url: The URL to check
            session: HTTP session for making requests

        Returns:
            Product name if it's a product page, None otherwise
        """
        self.logger.info(f"[PRODUCT_CHECK] Extracting content from {url} for AI analysis")

        try:
            # Extract page content
            page_content = extract_page_content(url, session)

            if not page_content["title"] and not page_content["text_content"]:
                self.logger.warning(f"[PRODUCT_CHECK] No content extracted from {url}")
                return None

            # Build AI prompt to check if this is a product page
            instruction_prompt = f"""You are now on a webpage. Here is the content:

Title: {page_content['title']}
Description: {page_content['description']}
URL: {page_content['url']}

Page Content:
{page_content['text_content']}

Is this the product description page itself? If yes, what is the product name?"""

            output_structure_prompt = """Please format your response as JSON with the following structure:
{
    "isProductPage": true/false,
    "productName": "Product Name Here" (only if isProductPage is true)
}"""

            self.logger.debug(f"[PRODUCT_CHECK] Sending AI prompt for product page detection")

            # Get AI response
            ai_response = send_ai_prompt(
                system_prompt=self.system_prompt,
                instruction_prompt=instruction_prompt,
                output_structure_prompt=output_structure_prompt,
                provider=self.ai_provider,
                model=self.ai_model,
                max_tokens=1000
            )

            self.logger.debug(f"[PRODUCT_CHECK] Raw AI response: {ai_response}")

            # Parse AI response
            try:
                # Try to find JSON in the response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1

                if start_idx == -1 or end_idx == 0:
                    self.logger.error(f"[PRODUCT_CHECK] No JSON found in AI response")
                    return None

                json_str = ai_response[start_idx:end_idx]
                result = json.loads(json_str)

                is_product_page = result.get("isProductPage", False)
                product_name = result.get("productName")

                self.logger.info(f"[PRODUCT_CHECK] AI Result - Product Page: {is_product_page}, "
                               f"Product: {product_name if product_name else 'N/A'}")

                if is_product_page and product_name:
                    return product_name.strip()

                return None

            except Exception as e:
                self.logger.error(f"[PRODUCT_CHECK] Error parsing AI response: {e}")
                return None

        except Exception as e:
            self.logger.error(f"[PRODUCT_CHECK] Error checking product page {url}: {e}")
            return None