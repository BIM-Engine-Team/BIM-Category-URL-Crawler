"""
Node processing functionality for web crawler.
Handles processing individual nodes and their children with AI scoring.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple

from .models import WebsiteNode, LinkInfo
from .utils import extract_link_info
from .ai_scoring import AIScoring


class NodeProcessor:
    """Handles processing of individual nodes and their children."""

    def __init__(self, ai_scoring: AIScoring, session, delay: float, discovered_urls: set):
        """
        Initialize node processor.

        Args:
            ai_scoring: AI scoring component
            session: HTTP session for making requests
            delay: Delay between requests
            discovered_urls: Set of already discovered URLs
        """
        self.ai_scoring = ai_scoring
        self.session = session
        self.delay = delay
        self.discovered_urls = discovered_urls
        self.logger = logging.getLogger(__name__)

    def process_node(self, node: WebsiteNode, products: List[Dict[str, str]],
                     url_to_node: Dict[str, WebsiteNode]) -> None:
        """
        DEPRECATED: This method is kept for backward compatibility only.
        Use process_node_with_children_info instead.
        """
        self.logger.warning("[PAGE_PROCESSING] DEPRECATED: process_node called. This method should not be used in the new architecture.")

        # Extract children links and their information for compatibility
        children_info = extract_link_info(node.url, self.session, self.discovered_urls)

        # Call the new method
        self.process_node_with_children_info(node, children_info, products, url_to_node)

        # Respect rate limiting
        time.sleep(self.delay)

    def _log_ai_score_summary(self, scores: List[Dict[str, Any]], children_info: List[LinkInfo]) -> None:
        """Log AI scoring results with color coding."""
        score_summary = []
        for i, link_info in enumerate(children_info):
            if i < len(scores):
                score = scores[i].get("score", 0.0)
                # Color code based on score ranges
                if score <= 1.0:
                    # Gray for very low scores (0-1)
                    colored_score = f"\033[90m{link_info.relative_path}: {score}\033[0m"
                elif score <= 5.0:
                    # Blue for low-medium scores (1-5)
                    colored_score = f"\033[94m{link_info.relative_path}: {score}\033[0m"
                elif score <= 9.0:
                    # Green for medium-high scores (5-9)
                    colored_score = f"\033[92m{link_info.relative_path}: {score}\033[0m"
                else:
                    # Yellow for high scores (>9)
                    colored_score = f"\033[93m{link_info.relative_path}: {score}\033[0m"
                score_summary.append(colored_score)
        self.logger.info(f"[AI_SCORES] {', '.join(score_summary)}")

    def _process_scored_links(self, children_info: List[LinkInfo], scores: List[Dict[str, Any]],
                             node: WebsiteNode, products: List[Dict[str, str]],
                             url_to_node: Dict[str, WebsiteNode]) -> Tuple[int, int, int]:
        """Process each child link with its AI score and return counts."""
        skipped_count = 0
        product_count = 0
        queued_count = 0

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
            child_node = self._create_child_node(link_info, node, score, product_name, url_to_node)

            # Handle scoring results
            if score < 1.0:
                # Very low score - mark as explored (skip)
                child_node.is_explored = True
                self.logger.debug(f"[PAGE_PROCESSING] SKIPPING '{link_info.title}' (score: {score} < 1.0)")
                skipped_count += 1
            elif score > 9.0:
                # Very high score - likely product page
                child_node.is_explored = True
                if product_name:
                    child_node.product_name = product_name
                    products.append({
                        "productName": product_name,
                        "url": link_info.url
                    })
                    self.logger.info(f"[PAGE_PROCESSING] ✓ PRODUCT FOUND: '{product_name}' at {link_info.url} (score: {score})")
                else:
                    self.logger.info(f"[PAGE_PROCESSING] ✓ HIGH SCORE but no product name: '{link_info.title}' (score: {score})")
                product_count += 1
            else:
                # Medium score - will be added to open set by caller
                self.logger.debug(f"[PAGE_PROCESSING] QUEUED for exploration: '{link_info.title}' (score: {score})")
                queued_count += 1
                # Store the child node for caller to add to open set
                if not hasattr(node, '_queued_children'):
                    node._queued_children = []
                node._queued_children.append(child_node)

        return skipped_count, product_count, queued_count

    def _create_child_node(self, link_info: LinkInfo, parent_node: WebsiteNode,
                          score: float, product_name: Optional[str],
                          url_to_node: Dict[str, WebsiteNode]) -> WebsiteNode:
        """Create a child node with the given score and product name."""
        if link_info.url in url_to_node:
            node = url_to_node[link_info.url]
        else:
            # Create new node
            node = WebsiteNode(link_info.url, link_info.relative_path, parent_node)
            parent_node.children[link_info.relative_path] = node
            url_to_node[link_info.url] = node

        node.score = score
        if product_name:
            node.product_name = product_name

        return node


    def process_node_with_children_info(self, node: WebsiteNode, children_info: List[LinkInfo],
                                       products: List[Dict[str, str]], url_to_node: Dict[str, WebsiteNode]) -> None:
        """
        Process a single node with pre-extracted children information.

        Args:
            node: The node to process
            children_info: Pre-extracted children link information (may include dynamic content)
            products: List to append found products to
            url_to_node: Mapping from URLs to nodes
        """
        if not children_info:
            self.logger.warning(f"[PAGE_PROCESSING] No links provided for {node.url}")
            return

        self.logger.info(f"[PAGE_PROCESSING] Processing {len(children_info)} links from {node.url} (including dynamic content)")
        for i, link in enumerate(children_info):
            self.logger.debug(f"[PAGE_PROCESSING] Link {i+1}: {link.relative_path} - '{link.title}' - {link.description[:100]}...")

        self.logger.info(f"[PAGE_PROCESSING] Sending AI prompt to score {len(children_info)} links from {node.url}")

        try:
            # Get AI response with retry logic
            scores = self.ai_scoring.get_ai_scores_with_retry(children_info)
            self.logger.info(f"[PAGE_PROCESSING] Got {len(scores)} AI scores for {node.url}")

            # Log AI scoring results in requested format with color coding
            self._log_ai_score_summary(scores, children_info)

            # Process each child with its score using ID-based matching
            skipped_count, product_count, queued_count = self._process_scored_links(
                children_info, scores, node, products, url_to_node
            )

            self.logger.info(f"[PAGE_PROCESSING] Processing complete for {node.url}: {skipped_count} skipped, {product_count} products found, {queued_count} queued")

        except Exception as e:
            self.logger.error(f"[PAGE_PROCESSING] Error processing node {node.url}: {e}")