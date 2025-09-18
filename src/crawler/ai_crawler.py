"""
AI-guided web crawler for product page discovery.
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import urlparse

from .models import WebsiteNode, OpenSet, LinkInfo
from .utils import extract_link_info, is_same_domain
from .dynamic_loading import DynamicLoadingHandler

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


class AIGuidedCrawler:
    """AI-guided web crawler that uses AI to prioritize exploration paths."""

    def __init__(self, base_url: str, delay: float = 1.0, max_pages: int = 50):
        """
        Initialize the AI-guided crawler.

        Args:
            base_url: The starting URL (homepage)
            delay: Delay between requests in seconds
            max_pages: Maximum number of pages to explore
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.delay = delay
        self.max_pages = max_pages

        # Tree structure
        self.root = WebsiteNode(base_url, "")
        self.url_to_node: Dict[str, WebsiteNode] = {base_url: self.root}

        # Open set for priority-based exploration
        self.open_set = OpenSet()

        # Final product results
        self.products: List[Dict[str, str]] = []

        # Set to track discovered URLs to avoid duplicates
        self.discovered_urls: set = {base_url}

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Setup session for better performance
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # System prompt for AI
        self.system_prompt = (
            "You are an architect. You want to find the product information from a supplier's website. "
            "You are clicking the button to go to the production description page."
        )

        # Dynamic loading handler
        self.dynamic_handler = DynamicLoadingHandler(self.domain, self.delay)

    def process_node(self, node: WebsiteNode) -> None:
        """
        Process a single node using AI to score its children.

        Args:
            node: The node to process
        """
        self.logger.info(f"[PAGE_PROCESSING] Starting to process node: {node.url}")

        # Mark this node as explored
        node.is_explored = True

        # Extract children links and their information
        children_info = extract_link_info(node.url, self.session, self.discovered_urls)

        if not children_info:
            self.logger.warning(f"[PAGE_PROCESSING] No links found on {node.url}")
            return

        self.logger.info(f"[PAGE_PROCESSING] Found {len(children_info)} links on {node.url}")
        for i, link in enumerate(children_info):
            self.logger.debug(f"[PAGE_PROCESSING] Link {i+1}: {link.relative_path} - '{link.title}' - {link.description[:100]}...")

        # Prepare prompt for AI scoring
        instruction_prompt = self._build_instruction_prompt(children_info)
        output_structure_prompt = self._build_output_structure_prompt()

        self.logger.info(f"[PAGE_PROCESSING] Sending AI prompt to score {len(children_info)} links from {node.url}")
        self.logger.debug(f"[PAGE_PROCESSING] AI System prompt: {self.system_prompt}")
        self.logger.debug(f"[PAGE_PROCESSING] AI Instruction prompt: {instruction_prompt}")
        self.logger.debug(f"[PAGE_PROCESSING] AI Output structure prompt: {output_structure_prompt}")

        try:
            # Get AI response with retry logic
            scores = self._get_ai_scores_with_retry(
                instruction_prompt=instruction_prompt,
                output_structure_prompt=output_structure_prompt,
                expected_count=len(children_info)
            )
            self.logger.info(f"[PAGE_PROCESSING] Got {len(scores)} AI scores for {node.url}")

            # Process each child with its score using ID-based matching
            for link_info in children_info:
                # Find the corresponding score by ID
                score_data = None
                for score_item in scores:
                    if score_item.get("id") == link_info.id:
                        score_data = score_item
                        break

                # Fallback if ID matching fails
                if score_data is None and link_info.id < len(scores):
                    score_data = scores[link_info.id]
                    self.logger.warning(f"[PAGE_PROCESSING] ID matching failed for link {link_info.id}, using positional fallback")

                # Final fallback
                if score_data is None:
                    score_data = {"id": link_info.id, "score": 0.0}
                    self.logger.warning(f"[PAGE_PROCESSING] No score found for link {link_info.id}, using default")

                score = score_data.get("score", 0.0)
                product_name = score_data.get("productName")

                self.logger.debug(f"[PAGE_PROCESSING] Link ID {link_info.id} '{link_info.title}' scored {score}" +
                                (f" with product name: {product_name}" if product_name else ""))

                # Create child node
                child_node = self._create_child_node(link_info, node, score, product_name)

                # Handle scoring results
                if score < 1.0:
                    # Very low score - mark as explored (skip)
                    child_node.is_explored = True
                    self.logger.debug(f"[PAGE_PROCESSING] SKIPPING '{link_info.title}' (score: {score} < 1.0)")
                elif score > 9.0:
                    # Very high score - likely product page
                    child_node.is_explored = True
                    if product_name:
                        child_node.product_name = product_name
                        self.products.append({
                            "productName": product_name,
                            "url": link_info.url
                        })
                        self.logger.info(f"[PAGE_PROCESSING] ✓ PRODUCT FOUND: '{product_name}' at {link_info.url} (score: {score})")
                    else:
                        self.logger.info(f"[PAGE_PROCESSING] ✓ HIGH SCORE but no product name: '{link_info.title}' (score: {score})")
                else:
                    # Medium score - add to open set for further exploration
                    self.open_set.add(child_node)
                    self.logger.debug(f"[PAGE_PROCESSING] QUEUED for exploration: '{link_info.title}' (score: {score})")

            # Summary of processing results
            skipped_count = sum(1 for score_data in scores if score_data.get("score", 0.0) < 1.0)
            product_count = sum(1 for score_data in scores if score_data.get("score", 0.0) > 9.0)
            queued_count = sum(1 for score_data in scores if 1.0 <= score_data.get("score", 0.0) <= 9.0)

            self.logger.info(f"[PAGE_PROCESSING] Processing complete for {node.url}: {skipped_count} skipped, {product_count} products found, {queued_count} queued")

            # Check for dynamic loading if we found products on this page
            if product_count > 0:
                self.logger.info(f"[PAGE_PROCESSING] Found {product_count} products on {node.url}, checking for dynamic loading...")
                try:
                    # Run dynamic loading check asynchronously
                    additional_links = asyncio.run(
                        self.dynamic_handler.check_and_exhaust_dynamic_loading(
                            node.url, children_info, self.discovered_urls
                        )
                    )

                    if additional_links:
                        self.logger.info(f"[PAGE_PROCESSING] Found {len(additional_links)} additional links via dynamic loading")

                        # Process additional links with AI scoring
                        additional_instruction_prompt = self._build_instruction_prompt(additional_links)
                        additional_output_structure_prompt = self._build_output_structure_prompt()

                        additional_scores = self._get_ai_scores_with_retry(
                            instruction_prompt=additional_instruction_prompt,
                            output_structure_prompt=additional_output_structure_prompt,
                            expected_count=len(additional_links)
                        )

                        # Process additional links
                        for link_info in additional_links:
                            # Find the corresponding score by ID
                            score_data = None
                            for score_item in additional_scores:
                                if score_item.get("id") == link_info.id:
                                    score_data = score_item
                                    break

                            if score_data is None and link_info.id < len(additional_scores):
                                score_data = additional_scores[link_info.id]

                            if score_data is None:
                                score_data = {"id": link_info.id, "score": 0.0}

                            score = score_data.get("score", 0.0)
                            product_name = score_data.get("productName")

                            # Create child node for additional link
                            child_node = self._create_child_node(link_info, node, score, product_name)

                            # Handle scoring results for additional links
                            if score < 1.0:
                                child_node.is_explored = True
                                self.logger.debug(f"[PAGE_PROCESSING] DYNAMIC: SKIPPING '{link_info.title}' (score: {score} < 1.0)")
                            elif score > 9.0:
                                child_node.is_explored = True
                                if product_name:
                                    child_node.product_name = product_name
                                    self.products.append({
                                        "productName": product_name,
                                        "url": link_info.url
                                    })
                                    self.logger.info(f"[PAGE_PROCESSING] DYNAMIC: ✓ PRODUCT FOUND: '{product_name}' at {link_info.url} (score: {score})")
                                else:
                                    self.logger.info(f"[PAGE_PROCESSING] DYNAMIC: ✓ HIGH SCORE but no product name: '{link_info.title}' (score: {score})")
                            else:
                                self.open_set.add(child_node)
                                self.logger.debug(f"[PAGE_PROCESSING] DYNAMIC: QUEUED for exploration: '{link_info.title}' (score: {score})")

                except Exception as e:
                    self.logger.error(f"[PAGE_PROCESSING] Error in dynamic loading check for {node.url}: {e}")

        except Exception as e:
            self.logger.error(f"[PAGE_PROCESSING] Error processing node {node.url}: {e}")

        # Respect rate limiting
        time.sleep(self.delay)

    def _build_instruction_prompt(self, children_info: List[LinkInfo]) -> str:
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

    def _build_output_structure_prompt(self) -> str:
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

    def _get_ai_scores_with_retry(self, instruction_prompt: str, output_structure_prompt: str, expected_count: int, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Get AI scores with retry logic for invalid responses.

        Args:
            instruction_prompt: The instruction prompt for AI
            output_structure_prompt: The output structure prompt
            expected_count: Expected number of score objects
            max_retries: Maximum number of retry attempts

        Returns:
            List of score dictionaries with proper ID-based matching
        """
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"[AI_RETRY] Attempt {attempt + 1}/{max_retries + 1} to get AI scores")

                # Get AI response
                ai_response = send_ai_prompt(
                    system_prompt=self.system_prompt,
                    instruction_prompt=instruction_prompt,
                    output_structure_prompt=output_structure_prompt,
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

    def _create_child_node(self, link_info: LinkInfo, parent_node: WebsiteNode,
                          score: float, product_name: Optional[str] = None) -> WebsiteNode:
        """Create a child node with the given score and product name."""
        if link_info.url in self.url_to_node:
            node = self.url_to_node[link_info.url]
        else:
            # Create new node
            node = WebsiteNode(link_info.url, link_info.relative_path, parent_node)
            parent_node.children[link_info.relative_path] = node
            self.url_to_node[link_info.url] = node

        node.score = score
        if product_name:
            node.product_name = product_name

        return node

    def crawl(self) -> List[Dict[str, str]]:
        """
        Main crawling method using AI-guided exploration.

        Returns:
            List of product dictionaries with productName and url
        """
        self.logger.info(f"Starting AI-guided crawl of {self.base_url}")
        self.logger.info(f"Domain scope: {self.domain}")

        # Add root node to open set to start exploration
        self.open_set.add(self.root)
        pages_processed = 0

        while not self.open_set.is_empty() and pages_processed < self.max_pages:
            # Get next node to process
            current_node = self.open_set.pop()
            if current_node is None:
                break

            # Skip if already explored
            if current_node.is_explored:
                continue

            # Process the node
            self.process_node(current_node)
            pages_processed += 1

            self.logger.info(f"Progress: {pages_processed} pages processed, "
                           f"{len(self.products)} products found, "
                           f"{self.open_set.size()} nodes in queue")

        self.logger.info(f"Crawl completed. Found {len(self.products)} products across {pages_processed} pages")
        return self.products

    def get_results(self) -> Dict[str, Any]:
        """Get detailed crawling results."""
        return {
            "products": self.products,
            "pages_processed": len([node for node in self.url_to_node.values() if node.is_explored]),
            "total_nodes": len(self.url_to_node),
            "base_url": self.base_url,
            "domain": self.domain
        }

    def save_results(self, filename: str = None) -> None:
        """Save crawling results to a JSON file."""
        if filename is None:
            filename = f"ai_crawl_results_{self.domain.replace('.', '_')}.json"

        results = self.get_results()

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Results saved to: {filename}")

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")