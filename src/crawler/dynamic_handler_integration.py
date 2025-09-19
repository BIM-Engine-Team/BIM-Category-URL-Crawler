"""
Dynamic loading handler integration for web crawler.
Handles the integration between main crawler and dynamic loading detection.
"""

import asyncio
import logging
from typing import List

from .models import WebsiteNode, LinkInfo
from .dynamic_loading import DynamicLoadingHandler
from .node_processor import NodeProcessor


class DynamicHandlerIntegration:
    """Handles dynamic loading detection and integration with node processing."""

    def __init__(self, domain: str, delay: float):
        """
        Initialize dynamic handler integration.

        Args:
            domain: The domain being crawled
            delay: Delay between requests
        """
        self.dynamic_handler = DynamicLoadingHandler(domain, delay)
        self.logger = logging.getLogger(__name__)

    def handle_dynamic_loading(self, node: WebsiteNode, node_processor: NodeProcessor,
                              products: List[dict], url_to_node: dict,
                              discovered_urls: set) -> None:
        """
        Handle dynamic loading detection and processing for a node.

        Args:
            node: The node that was processed
            node_processor: Node processor instance
            products: List to append found products to
            url_to_node: Mapping from URLs to nodes
            discovered_urls: Set of discovered URLs
        """
        # Check if node has processing results indicating products were found
        if not hasattr(node, '_processing_results'):
            return

        processing_results = node._processing_results
        product_count = processing_results.get('product_count', 0)
        children_info = processing_results.get('children_info', [])

        if product_count > 0:
            self.logger.info(f"[PAGE_PROCESSING] Found {product_count} products on {node.url}, checking for dynamic loading...")

            try:
                # Run dynamic loading check asynchronously
                additional_links = asyncio.run(
                    self.dynamic_handler.check_and_exhaust_dynamic_loading(
                        node.url, children_info, discovered_urls
                    )
                )

                if additional_links:
                    # Process additional links using the node processor
                    node_processor.process_additional_links(
                        additional_links, node, products, url_to_node
                    )

            except Exception as e:
                self.logger.error(f"[PAGE_PROCESSING] Error in dynamic loading check for {node.url}: {e}")

        # Clean up processing results to free memory
        if hasattr(node, '_processing_results'):
            delattr(node, '_processing_results')