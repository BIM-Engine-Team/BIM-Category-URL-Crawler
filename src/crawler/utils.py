"""
Utility functions for the website crawler.
"""

from urllib.parse import urlparse, urljoin
import logging
import re
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


def _create_link_info(href: str, element, base_url: str, link_id: int, discovered_urls: Optional[set] = None, element_type: str = "link") -> Optional[LinkInfo]:
    """
    Helper function to create LinkInfo from an element and href.

    Args:
        href: The URL or href value
        element: The BeautifulSoup element
        base_url: The base URL for resolving relative URLs
        link_id: Unique identifier for the link
        discovered_urls: Set of already discovered URLs
        element_type: Type of element (for description)

    Returns:
        LinkInfo object or None if invalid
    """
    # Get absolute URL
    absolute_url = urljoin(base_url, href)

    # Skip if this URL has already been discovered
    if discovered_urls is not None and absolute_url in discovered_urls:
        return None

    # Only include links from the same domain
    if not is_same_domain(absolute_url, base_url):
        return None

    # Extract title from various sources
    title = ""
    if element.get('title'):
        title = element['title'].strip()
    elif element.get('alt'):  # For images and areas
        title = element['alt'].strip()
    elif element.get('value'):  # For inputs
        title = element['value'].strip()
    elif element.get_text(strip=True):
        title = element.get_text(strip=True)
    elif element.name == 'form':
        # For forms, try to get title from nearby headings or labels
        form_text = element.get_text(strip=True)[:50]
        title = f"Form: {form_text}" if form_text else "Form submission"

    # Extract link text (visible text content)
    link_text = element.get_text(strip=True) if element.get_text(strip=True) else ""

    # Extract description from various sources
    description = ""
    if element.get('aria-label'):
        description = element['aria-label'].strip()
    elif element.get('placeholder'):  # For form inputs
        description = element['placeholder'].strip()
    elif element_type == "form":
        # For forms, get method and input types
        method = element.get('method', 'GET').upper()
        inputs = element.find_all(['input', 'select', 'textarea'])
        input_types = [inp.get('type', inp.name) for inp in inputs[:3]]
        description = f"{method} form with: {', '.join(input_types)}" if input_types else f"{method} form"
    else:
        # Try to get description from parent element or nearby text
        parent = element.parent
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
        id=link_id,  # Assign unique ID for matching
        link_tag=str(element),  # The HTML link tag content
        link_text=link_text[:100]  # The visible text content of the link
    )

    # Add to discovered URLs set to avoid future duplicates
    if discovered_urls is not None:
        discovered_urls.add(absolute_url)

    return link_info


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

        # Find all navigable elements
        link_id = 0

        # 1. Standard anchor tags with href attributes
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href'].strip()
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(href, link_tag, url, link_id, discovered_urls)
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        # 2. Image map areas
        for area_tag in soup.find_all('area', href=True):
            href = area_tag['href'].strip()
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(href, area_tag, url, link_id, discovered_urls)
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        # 3. Forms with action attributes
        for form_tag in soup.find_all('form', action=True):
            action = form_tag['action'].strip()
            if action and not action.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(action, form_tag, url, link_id, discovered_urls, element_type="form")
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        # 4. Buttons with formaction
        for button_tag in soup.find_all('button', formaction=True):
            formaction = button_tag['formaction'].strip()
            if formaction and not formaction.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(formaction, button_tag, url, link_id, discovered_urls)
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        # 5. Elements with data attributes (data-href, data-url, data-link)
        data_attrs = ['data-href', 'data-url', 'data-link', 'data-target']
        for attr in data_attrs:
            for element in soup.find_all(attrs={attr: True}):
                data_url = element.get(attr, '').strip()
                if data_url and not data_url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    link_info = _create_link_info(data_url, element, url, link_id, discovered_urls)
                    if link_info:
                        link_infos.append(link_info)
                        link_id += 1

        # 6. Clickable elements with onclick containing location or window.open
        onclick_pattern = re.compile(r'(?:location\.href|window\.open)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)
        for element in soup.find_all(attrs={"onclick": True}):
            onclick = element.get('onclick', '')
            match = onclick_pattern.search(onclick)
            if match:
                js_url = match.group(1).strip()
                if js_url and not js_url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    link_info = _create_link_info(js_url, element, url, link_id, discovered_urls)
                    if link_info:
                        link_infos.append(link_info)
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