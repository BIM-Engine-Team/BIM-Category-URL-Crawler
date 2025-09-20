"""
Result cleaner module to remove duplicate products using AI analysis.
"""

import json
import logging
import os
from typing import List, Dict, Any
from pathlib import Path

from .ai_client.ai_middleware import send_ai_prompt


class ResultCleaner:
    """AI-powered duplicate result cleaner for crawler outputs."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt from system_prompt.json."""
        try:
            prompt_path = Path(__file__).parent.parent / "crawler" / "system_prompt.json"
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
            return prompt_data.get("prompt", "You are an architect looking for product information.")
        except Exception as e:
            self.logger.warning(f"Could not load system prompt: {e}")
            return "You are an architect looking for product information."

    def clean_duplicates(self, input_file: str, output_file: str = None) -> str:
        """
        Clean duplicate products from crawler results using AI analysis.

        Args:
            input_file: Path to the input JSON file with crawler results
            output_file: Path to save cleaned results (optional)

        Returns:
            Path to the cleaned results file
        """
        self.logger.info(f"[RESULT_CLEANER] Starting duplicate cleaning for: {input_file}")

        # Load input results
        results = self._load_results(input_file)
        products = results.get("products", [])

        if not products:
            self.logger.warning(f"[RESULT_CLEANER] No products found in {input_file}")
            return input_file

        self.logger.info(f"[RESULT_CLEANER] Found {len(products)} products to analyze")

        # Clean duplicates using AI
        cleaned_products = self._clean_duplicates_with_ai(products)

        # Update results
        results["products"] = cleaned_products

        # Generate output filename if not provided
        if output_file is None:
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")

        # Save cleaned results
        self._save_results(results, output_file)

        duplicates_removed = len(products) - len(cleaned_products)
        self.logger.info(f"[RESULT_CLEANER] Cleaning completed: {duplicates_removed} duplicates removed")
        self.logger.info(f"[RESULT_CLEANER] Cleaned results saved to: {output_file}")

        return output_file

    def _load_results(self, file_path: str) -> Dict[str, Any]:
        """Load results from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Results file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in results file {file_path}: {e}")

    def _clean_duplicates_with_ai(self, products: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Use AI to identify and remove duplicate products."""
        if len(products) <= 1:
            return products

        # Create instruction prompt
        products_json = json.dumps(products, indent=2)
        instruction_prompt = f"""You have found the following products but some of them are duplicated. Judge from the product name and URL to detect any duplicated product. For duplicated products, just keep the one who has the main URL (without fragments like #ratings-and-reviews, #specifications, etc.).

The products you found are listed here:
{products_json}"""

        # Create output structure prompt
        output_structure_prompt = """Return the cleaned products as a JSON array with the following structure:
[
  {
    "productName": "Product Name Here",
    "url": "https://example.com/product-url"
  }
]

Each product object must have exactly these two fields:
- productName: string containing the product name
- url: string containing the product URL

Return only the JSON array, no additional text or explanation."""

        try:
            self.logger.info(f"[RESULT_CLEANER] Sending {len(products)} products to AI for duplicate analysis")

            response = send_ai_prompt(
                system_prompt=self.system_prompt,
                instruction_prompt=instruction_prompt,
                output_structure_prompt=output_structure_prompt,
                max_tokens=8000
            )

            # Parse AI response
            cleaned_products = self._parse_ai_response(response)

            self.logger.info(f"[RESULT_CLEANER] AI analysis completed: {len(cleaned_products)} products after cleaning")
            return cleaned_products

        except Exception as e:
            self.logger.error(f"[RESULT_CLEANER] AI duplicate cleaning failed: {e}")
            self.logger.info("[RESULT_CLEANER] Falling back to original products")
            return products

    def _parse_ai_response(self, response: str) -> List[Dict[str, str]]:
        """Parse AI response to extract cleaned product list."""
        try:
            # Try to find JSON array in the response
            response = response.strip()

            # Handle cases where AI might wrap JSON in markdown code blocks
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # Parse JSON
            cleaned_products = json.loads(response)

            # Validate structure
            if not isinstance(cleaned_products, list):
                raise ValueError("Response is not a JSON array")

            for product in cleaned_products:
                if not isinstance(product, dict):
                    raise ValueError("Product is not a JSON object")
                if "productName" not in product or "url" not in product:
                    raise ValueError("Product missing required fields")

            return cleaned_products

        except Exception as e:
            self.logger.error(f"[RESULT_CLEANER] Failed to parse AI response: {e}")
            self.logger.debug(f"[RESULT_CLEANER] AI Response: {response}")
            raise ValueError(f"Invalid AI response format: {e}")

    def _save_results(self, results: Dict[str, Any], file_path: str) -> None:
        """Save cleaned results to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save cleaned results to {file_path}: {e}")


def clean_crawler_results(input_file: str, output_file: str = None) -> str:
    """
    Convenience function to clean duplicate products from crawler results.

    Args:
        input_file: Path to the input JSON file with crawler results
        output_file: Path to save cleaned results (optional)

    Returns:
        Path to the cleaned results file
    """
    cleaner = ResultCleaner()
    return cleaner.clean_duplicates(input_file, output_file)