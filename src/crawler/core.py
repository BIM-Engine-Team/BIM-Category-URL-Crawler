"""
Core crawler functionality.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Set, Dict
import logging
from collections import deque

from .models import WebsiteNode


class WebsiteCrawler:
    """Main website crawler class with tree structure and BFS."""

    def __init__(self, base_url: str, delay: float = 1.0, max_pages: int = 100):
        """
        Initialize the website crawler.

        Args:
            base_url: The starting URL (homepage)
            delay: Delay between requests in seconds
            max_pages: Maximum number of pages to crawl
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.delay = delay
        self.max_pages = max_pages

        self.visited_urls: Set[str] = set()
        self.found_links: Set[str] = set()
        self.to_visit: deque = deque([base_url])  # Using deque for BFS

        # Tree structure
        self.root = WebsiteNode(base_url, "")
        self.url_to_node: Dict[str, WebsiteNode] = {base_url: self.root}

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Setup session for better performance
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc == self.domain or parsed_url.netloc == ''
        except:
            return False

    def normalize_url(self, url: str, base_url: str) -> str:
        """Convert relative URLs to absolute and normalize."""
        # Join with base URL to handle relative paths
        absolute_url = urljoin(base_url, url)

        # Parse and reconstruct to normalize
        parsed = urlparse(absolute_url)

        # Remove fragment (anchor) and normalize
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"

        return normalized

    def extract_links(self, url: str) -> Set[str]:
        """Extract all links from a given URL."""
        try:
            self.logger.info(f"Crawling: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            links = set()

            # Find all anchor tags with href attributes
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()

                # Skip empty links, javascript, mailto, tel, etc.
                if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    continue

                # Normalize the URL
                normalized_url = self.normalize_url(href, url)

                # Only include links from the same domain
                if self.is_same_domain(normalized_url):
                    links.add(normalized_url)

            return links

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error crawling {url}: {e}")
            return set()
        except Exception as e:
            self.logger.error(f"Unexpected error crawling {url}: {e}")
            return set()

    def get_path_from_url(self, url: str) -> str:
        """Extract path from URL for tree structure."""
        try:
            parsed = urlparse(url)
            path = parsed.path
            if parsed.query:
                path += f"?{parsed.query}"
            return path if path != "/" else ""
        except:
            return url

    def find_or_create_node(self, url: str, parent_url: str) -> WebsiteNode:
        """Find existing node or create new one in the tree."""
        if url in self.url_to_node:
            return self.url_to_node[url]

        path = self.get_path_from_url(url)
        parent_node = self.url_to_node.get(parent_url, self.root)

        # Create new node as child of parent
        node = parent_node.add_child(url, path)
        self.url_to_node[url] = node
        return node

    def crawl(self) -> WebsiteNode:
        """
        Main crawling method using breadth-first search.

        Returns:
            Root node of the website tree
        """
        self.logger.info(f"Starting crawl of {self.base_url}")
        self.logger.info(f"Domain scope: {self.domain}")

        while self.to_visit and len(self.visited_urls) < self.max_pages:
            current_url = self.to_visit.popleft()  # BFS: take from left

            # Skip if already visited
            if current_url in self.visited_urls:
                continue

            # Mark as visited and explored
            self.visited_urls.add(current_url)
            if current_url in self.url_to_node:
                self.url_to_node[current_url].is_explored = True

            # Extract links from current page
            page_links = self.extract_links(current_url)

            # Add new links to our found_links set
            self.found_links.update(page_links)

            # Add unvisited links to the queue and tree structure
            for link in page_links:
                if link not in self.visited_urls and link not in self.to_visit:
                    self.to_visit.append(link)
                    # Create node in tree structure
                    self.find_or_create_node(link, current_url)

            # Respect rate limiting
            time.sleep(self.delay)

            self.logger.info(f"Progress: {len(self.visited_urls)} pages visited, {len(self.found_links)} unique links found")

        self.logger.info(f"Crawl completed. Found {len(self.found_links)} unique links across {len(self.visited_urls)} pages")
        return self.root

    def _get_max_depth(self) -> int:
        """Get the maximum depth in the tree."""
        max_depth = 0

        def traverse(node: WebsiteNode):
            nonlocal max_depth
            max_depth = max(max_depth, node.depth)
            for child in node.children.values():
                traverse(child)

        traverse(self.root)
        return max_depth

    def print_tree(self):
        """Print the tree structure to console."""
        print(f"\nWebsite Tree for: {self.base_url}")
        print(f"Total nodes: {len(self.url_to_node)}")
        print(f"Pages explored: {len(self.visited_urls)}")
        print(f"Max depth: {self._get_max_depth()}")
        print("\nLegend: ✓ = explored, ○ = discovered but not explored")
        print("Format: [explored_children/total_children explored]\n")
        print(self.root.get_tree_display())

    def save_results(self, filename: str = None):
        """Save crawling results to a file in tree format."""
        if filename is None:
            filename = f"crawl_tree_{self.domain.replace('.', '_')}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Website Crawl Tree for: {self.base_url}\n")
                f.write(f"Domain: {self.domain}\n")
                f.write(f"Pages Visited: {len(self.visited_urls)}\n")
                f.write(f"Unique Links Found: {len(self.found_links)}\n")
                f.write(f"Max Depth: {self._get_max_depth()}\n")
                f.write("="*70 + "\n\n")
                f.write("Legend: ✓ = explored, ○ = discovered but not explored\n")
                f.write("Format: [explored_children/total_children explored]\n\n")

                # Write tree structure
                f.write(self.root.get_tree_display())

                f.write("\n\n" + "="*70 + "\n")
                f.write("All URLs (flat list):\n\n")

                # Also include flat list for reference
                sorted_links = sorted(self.found_links)
                for link in sorted_links:
                    status = "✓" if link in self.visited_urls else "○"
                    f.write(f"{status} {link}\n")

            self.logger.info(f"Results saved to: {filename}")

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")