"""
Test script for dynamic loading functionality.
"""

import sys
import os
import asyncio
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crawler.dynamic_loading import DynamicLoadingHandler
from crawler.models import LinkInfo


def create_test_link_info(id: int, url: str, relative_path: str, title: str, link_text: str) -> LinkInfo:
    """Create a test LinkInfo object."""
    return LinkInfo(
        url=url,
        relative_path=relative_path,
        title=title,
        description=f"Description for {title}",
        id=id,
        link_tag=f'<a href="{relative_path}">{link_text}</a>',
        link_text=link_text
    )


async def test_dynamic_loading_handler():
    """Test the dynamic loading handler."""

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Starting dynamic loading handler test...")

    # Create test handler
    handler = DynamicLoadingHandler("example.com", delay=0.5)

    # Create test children info
    test_children = [
        create_test_link_info(0, "https://example.com/product1", "/product1", "Product 1", "View Product 1"),
        create_test_link_info(1, "https://example.com/next", "/next", "Next Page", "Next"),
        create_test_link_info(2, "https://example.com/load-more", "/load-more", "Load More", "Load More Products"),
        create_test_link_info(3, "https://example.com/tab1", "/tab1", "Tab 1", "Category 1"),
    ]

    # Test AI check (this will use the actual AI if available, or fail gracefully)
    try:
        logger.info("Testing AI dynamic loading detection...")

        # Mock some children info for AI
        pruned_children = []
        for link_info in test_children:
            pruned_children.append({
                "id": link_info.id,
                "relative_path": link_info.relative_path,
                "link_tag": link_info.link_tag,
                "link_text": link_info.link_text
            })

        dynamic_elements = await handler._check_with_ai(pruned_children)
        logger.info(f"AI detected dynamic elements: {dynamic_elements}")

    except Exception as e:
        logger.warning(f"AI check failed (expected without proper API key): {e}")

    # Test element finding logic
    logger.info("Testing element finding logic...")

    # Test with a simple HTML page (this would require a real browser)
    test_url = "https://httpbin.org/html"  # Simple HTML page for testing
    discovered_urls = set()

    try:
        logger.info(f"Testing dynamic loading check with {test_url}")
        additional_links = await handler.check_and_exhaust_dynamic_loading(
            test_url, test_children, discovered_urls
        )
        logger.info(f"Found {len(additional_links)} additional links: {[link.url for link in additional_links]}")

    except Exception as e:
        logger.error(f"Dynamic loading check failed: {e}")

    logger.info("Dynamic loading handler test completed.")


def test_ai_crawler_integration():
    """Test integration with AI crawler."""

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Testing AI crawler integration...")

    try:
        from crawler.ai_crawler import AIGuidedCrawler

        # Create a test crawler
        crawler = AIGuidedCrawler("https://httpbin.org", delay=0.5, max_pages=1)

        # Check that dynamic handler was initialized
        assert hasattr(crawler, 'dynamic_handler'), "Dynamic handler not initialized"
        assert crawler.dynamic_handler is not None, "Dynamic handler is None"

        logger.info("✓ AI crawler integration test passed - dynamic handler is properly initialized")

        # Test that asyncio import works
        try:
            import asyncio
            logger.info("✓ Asyncio import successful")
        except ImportError as e:
            logger.error(f"✗ Asyncio import failed: {e}")

    except ImportError as e:
        logger.error(f"✗ Failed to import AI crawler: {e}")
    except Exception as e:
        logger.error(f"✗ AI crawler integration test failed: {e}")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Dynamic Loading Implementation Test")
    print("=" * 50)

    # Test 1: Integration test
    test_ai_crawler_integration()

    print("\n" + "=" * 50)

    # Test 2: Dynamic loading handler (async)
    try:
        asyncio.run(test_dynamic_loading_handler())
    except Exception as e:
        print(f"Async test failed: {e}")

    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    main()