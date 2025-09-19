"""
AI-guided web crawler for product page discovery.
"""

import json
import logging
from typing import List, Dict, Any
import requests
from urllib.parse import urlparse

from .models import WebsiteNode, OpenSet
from .ai_scoring import AIScoring
from .node_processor import NodeProcessor
from .dynamic_handler_integration import DynamicHandlerIntegration


class AIGuidedCrawler:
    """AI-guided web crawler that uses AI to prioritize exploration paths."""

    def __init__(self, base_url: str, delay: float = 1.0, max_pages: int = 50,
                 ai_provider: str = None, ai_model: str = None):
        """
        Initialize the AI-guided crawler.

        Args:
            base_url: The starting URL (homepage)
            delay: Delay between requests in seconds
            max_pages: Maximum number of pages to explore
            ai_provider: AI provider to use (overrides config.json)
            ai_model: AI model to use (overrides config.json)
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
        system_prompt = (
            "You are an architect. You want to find the product information from a supplier's website. "
            "You are clicking the button to go to the production description page."
        )

        # Initialize components
        self.ai_scoring = AIScoring(system_prompt, ai_provider, ai_model)
        self.node_processor = NodeProcessor(self.ai_scoring, self.session, self.delay, self.discovered_urls)
        self.dynamic_handler_integration = DynamicHandlerIntegration(self.domain, self.delay)

    def process_node(self, node: WebsiteNode) -> None:
        """
        Process a single node using AI to score its children.

        Args:
            node: The node to process
        """
        # Use the node processor to handle the main processing logic
        self.node_processor.process_node(node, self.products, self.url_to_node)

        # Add any queued children to the open set
        if hasattr(node, '_queued_children'):
            for child_node in node._queued_children:
                self.open_set.add(child_node)
            delattr(node, '_queued_children')

        # Handle dynamic loading if products were found
        self.dynamic_handler_integration.handle_dynamic_loading(
            node, self.node_processor, self.products, self.url_to_node, self.discovered_urls
        )

        # Add any additional queued children from dynamic loading to the open set
        if hasattr(node, '_queued_children'):
            for child_node in node._queued_children:
                self.open_set.add(child_node)
            delattr(node, '_queued_children')


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