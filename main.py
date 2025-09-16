#!/usr/bin/env python3
"""
Website Crawler Main Script

Usage: python main.py <homepage_url>
Example: python main.py https://example.com
"""

import sys
from src.crawler import WebsiteCrawler


def main():
    """Main entry point for the website crawler."""
    if len(sys.argv) != 2:
        print("Usage: python main.py <homepage_url>")
        print("Example: python main.py https://example.com")
        sys.exit(1)

    homepage_url = sys.argv[1]

    # Create crawler instance
    crawler = WebsiteCrawler(
        base_url=homepage_url,
        delay=1.0,  # 1 second between requests
        max_pages=300  # Limit to prevent excessive crawling
    )

    # Start crawling
    root_node = crawler.crawl()

    # Print tree to console
    crawler.print_tree()

    # Save results
    crawler.save_results()

    print(f"\nCrawling completed!")
    print(f"Found {len(crawler.found_links)} unique links")
    print(f"Results saved to file")


if __name__ == "__main__":
    main()