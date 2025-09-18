"""
Test script for the AI-guided crawler implementation.
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from crawler.ai_crawler import AIGuidedCrawler


def test_crawler():
    """Test the AI crawler with a simple example."""
    print("Testing AI-guided crawler implementation...")

    # Test with a simple website (using a test config)
    test_url = "https://httpbin.org"  # Simple test site

    print(f"Initializing crawler for: {test_url}")

    try:
        crawler = AIGuidedCrawler(
            base_url=test_url,
            delay=0.5,
            max_pages=5  # Keep it small for testing
        )

        print("Crawler initialized successfully")
        print("Data structures created:")
        print(f"  - Root node: {crawler.root.url}")
        print(f"  - Open set: {type(crawler.open_set).__name__}")
        print(f"  - Products list: {len(crawler.products)} items")

        # Test the open set functionality
        print("\nTesting OpenSet:")
        test_node = crawler.root
        test_node.score = 5.0
        crawler.open_set.add(test_node)
        print(f"  - Added root node, open set size: {crawler.open_set.size()}")

        popped_node = crawler.open_set.pop()
        print(f"  - Popped node: {popped_node.url if popped_node else 'None'}")
        print(f"  - Open set size after pop: {crawler.open_set.size()}")

        print("\nAI-guided crawler test completed successfully!")
        return True

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_config():
    """Test loading task configuration."""
    print("\nTesting task configuration loading...")

    # Create a test config
    test_config = {
        "url": "https://example.com",
        "delay": 1.0,
        "max_pages": 10,
        "output": "test_results.json"
    }

    config_path = "test_config.json"

    try:
        # Write test config
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)

        # Test loading
        from src.main import load_task_config
        loaded_config = load_task_config(config_path)

        print("Task config loaded successfully:")
        for key, value in loaded_config.items():
            print(f"  {key}: {value}")

        # Cleanup
        os.remove(config_path)

        print("Task configuration test completed successfully!")
        return True

    except Exception as e:
        print(f"Error during config test: {e}")
        # Cleanup on error
        if os.path.exists(config_path):
            os.remove(config_path)
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("AI-GUIDED WEB CRAWLER TEST")
    print("=" * 50)

    success = True

    # Test crawler implementation
    success &= test_crawler()

    # Test task config functionality
    success &= test_task_config()

    print("\n" + "=" * 50)
    if success:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 50)