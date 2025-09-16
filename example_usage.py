#!/usr/bin/env python3
"""
Example usage of the Website Crawler utility
"""

from src.crawler import WebsiteCrawler

def example_crawl():
    """Example of how to use the WebsiteCrawler class."""

    # Example 1: Basic usage
    print("Example 1: Basic crawling")
    crawler = WebsiteCrawler(
        base_url="https://example.com",
        delay=1.0,      # Wait 1 second between requests
        max_pages=50    # Limit to 50 pages to avoid excessive crawling
    )

    # Perform the crawl
    root_node = crawler.crawl()

    # Print tree structure to console
    crawler.print_tree()

    # Save results to file
    crawler.save_results("example_crawl.txt")

    # Print summary
    print(f"\nFound {len(crawler.found_links)} unique links")
    print(f"Tree depth: {crawler._get_max_depth()}")

    print("\n" + "="*50 + "\n")

    # Example 2: Faster crawling with higher limits
    print("Example 2: More aggressive crawling")
    fast_crawler = WebsiteCrawler(
        base_url="https://httpbin.org",
        delay=0.5,      # Faster crawling
        max_pages=20    # Smaller site, fewer pages
    )

    fast_root = fast_crawler.crawl()
    fast_crawler.print_tree()
    fast_crawler.save_results("httpbin_crawl.txt")

    print(f"Found {len(fast_crawler.found_links)} unique links")

def crawl_specific_site(url: str):
    """Crawl a specific website provided by user."""
    print(f"Crawling website: {url}")

    crawler = WebsiteCrawler(
        base_url=url,
        delay=1.0,
        max_pages=100
    )

    root_node = crawler.crawl()

    # Print tree structure
    crawler.print_tree()

    # Create filename based on domain
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace('.', '_')
    filename = f"crawl_tree_{domain}.txt"

    crawler.save_results(filename)

    print(f"\nCrawling Results:")
    print(f"- Total links found: {len(crawler.found_links)}")
    print(f"- Pages visited: {len(crawler.visited_urls)}")
    print(f"- Tree depth: {crawler._get_max_depth()}")
    print(f"- Results saved to: {filename}")

    return root_node

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        # Crawl specific URL provided as command line argument
        url = sys.argv[1]
        crawl_specific_site(url)
    else:
        # Run examples
        print("Running example crawls...")
        example_crawl()

        print("\nTo crawl a specific website, run:")
        print("python example_usage.py <website_url>")
        print("Example: python example_usage.py https://example.com")