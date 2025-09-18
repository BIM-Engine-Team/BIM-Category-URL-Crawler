"""
Utility functions for the website crawler.
"""

from urllib.parse import urlparse, urljoin
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from .models import LinkInfo


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def is_valid_url(url: str) -> bool:
    """Check if URL is valid and has required components."""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by replacing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format byte size into human readable format."""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def extract_path_components(url: str) -> list:
    """Extract path components from URL."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return []
        return path.split('/')
    except Exception:
        return []


def extract_link_info(url: str, session: Optional[requests.Session] = None, discovered_urls: Optional[set] = None) -> List[LinkInfo]:
    """
    Extract detailed link information from a page.

    Args:
        url: The URL to extract links from
        session: Optional requests session for connection reuse
        discovered_urls: Optional set of already discovered URLs to avoid duplicates

    Returns:
        List of LinkInfo objects containing url, relative_path, title, and description
    """
    if session is None:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        link_infos = []

        # Find all anchor tags with href attributes
        link_id = 0
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href'].strip()

            # Skip empty links, javascript, mailto, tel, etc.
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            # Get absolute URL
            absolute_url = urljoin(url, href)

            # Skip if this URL has already been discovered
            if discovered_urls is not None and absolute_url in discovered_urls:
                continue

            # Only include links from the same domain
            if not is_same_domain(absolute_url, url):
                continue

            # Extract title (link text or title attribute)
            title = ""
            if link_tag.get('title'):
                title = link_tag['title'].strip()
            elif link_tag.get_text(strip=True):
                title = link_tag.get_text(strip=True)

            # Extract description from surrounding context or aria-label
            description = ""
            if link_tag.get('aria-label'):
                description = link_tag['aria-label'].strip()
            else:
                # Try to get description from parent element or nearby text
                parent = link_tag.parent
                if parent:
                    parent_text = parent.get_text(strip=True)
                    # Use parent text as description if it's reasonable length
                    if len(parent_text) < 200 and parent_text != title:
                        description = parent_text

            # Get relative path
            parsed_url = urlparse(absolute_url)
            relative_path = parsed_url.path
            if parsed_url.query:
                relative_path += f"?{parsed_url.query}"

            link_info = LinkInfo(
                url=absolute_url,
                relative_path=relative_path,
                title=title[:100],  # Limit title length
                description=description[:200],  # Limit description length
                id=link_id  # Assign unique ID for matching
            )

            link_infos.append(link_info)

            # Add to discovered URLs set to avoid future duplicates
            if discovered_urls is not None:
                discovered_urls.add(absolute_url)

            link_id += 1

        return link_infos

    except Exception as e:
        logging.error(f"Error extracting links from {url}: {e}")
        return []


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain."""
    try:
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2 or domain1 == '' or domain2 == ''
    except Exception:
        return False