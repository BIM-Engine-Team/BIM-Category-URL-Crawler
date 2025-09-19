"""
Utility functions for the website crawler.
"""

from urllib.parse import urlparse, urljoin
import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from .models import LinkInfo, DynamicElementInfo


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


def extract_link_info_from_html(html_content: str, base_url: str, discovered_urls: Optional[set] = None, start_id: int = 0) -> List[LinkInfo]:
    """
    Extract link information from HTML content.

    Args:
        html_content: The HTML content to parse
        base_url: The base URL for resolving relative URLs
        discovered_urls: Optional set of already discovered URLs to avoid duplicates
        start_id: Starting ID for link numbering

    Returns:
        List of LinkInfo objects
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        link_infos = []
        link_id = start_id

        # 1. Standard anchor tags with href attributes
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href'].strip()
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(href, link_tag, base_url, link_id, discovered_urls)
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        # 2. Image map areas
        for area_tag in soup.find_all('area', href=True):
            href = area_tag['href'].strip()
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(href, area_tag, base_url, link_id, discovered_urls)
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        # 3. Forms with action attributes
        for form_tag in soup.find_all('form', action=True):
            action = form_tag['action'].strip()
            if action and not action.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                link_info = _create_link_info(action, form_tag, base_url, link_id, discovered_urls, element_type="form")
                if link_info:
                    link_infos.append(link_info)
                    link_id += 1

        return link_infos

    except Exception as e:
        logging.error(f"Error extracting links from HTML content: {e}")
        return []


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain."""
    try:
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2 or domain1 == '' or domain2 == ''
    except Exception:
        return False


def extract_page_content(url: str, session: Optional[requests.Session] = None) -> dict:
    """
    Extract title, description, and text content from a webpage for AI analysis.

    Args:
        url: The URL to extract content from
        session: Optional requests session for connection reuse

    Returns:
        Dictionary containing title, description, and text content
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

        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract meta description
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()

        # If no meta description, try to get from other sources
        if not description:
            # Try h1 tag
            h1_tag = soup.find('h1')
            if h1_tag:
                description = h1_tag.get_text(strip=True)
            # Try first paragraph
            elif soup.find('p'):
                first_p = soup.find('p')
                description = first_p.get_text(strip=True)[:200]

        # Extract main text content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text_content = soup.get_text()

        # Clean up text content
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)

        # Limit text content to reasonable size for AI processing
        if len(text_content) > 3000:
            text_content = text_content[:3000] + "..."

        return {
            "title": title,
            "description": description,
            "text_content": text_content,
            "url": url
        }

    except Exception as e:
        logging.error(f"Error extracting content from {url}: {e}")
        return {
            "title": "",
            "description": "",
            "text_content": "",
            "url": url
        }


def extract_dynamic_elements(url: str, session: Optional[requests.Session] = None) -> List[DynamicElementInfo]:
    """
    Extract potentially dynamic elements from a page for AI analysis using requests.

    This function focuses on interactive elements that might trigger dynamic loading,
    such as buttons, clickable divs, and other elements with event handlers.
    Uses requests for fast initial extraction, Playwright is used later for actual interaction.

    Args:
        url: The URL to extract elements from
        session: Optional requests session for connection reuse

    Returns:
        List of DynamicElementInfo objects containing element metadata for AI analysis
    """
    if session is None:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return extract_dynamic_elements_from_html(response.text, url)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error extracting dynamic elements from {url}: {e}")
        return []


def extract_dynamic_elements_from_html(html_content: str, base_url: str) -> List[DynamicElementInfo]:
    """
    Extract potentially dynamic elements from HTML content using BeautifulSoup.

    Args:
        html_content: The HTML content to parse
        base_url: The base URL for context

    Returns:
        List of DynamicElementInfo objects
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    dynamic_elements = []
    element_id = 0

    # Define selectors for potentially dynamic elements
    selectors = [
        'button',  # Buttons
        '[onclick]',  # Elements with onclick handlers
        '[class*="next"]',  # Elements with "next" in class name
        '[class*="more"]',  # Elements with "more" in class name
        '[class*="load"]',  # Elements with "load" in class name
        '[class*="page"]',  # Elements with "page" in class name
        '[class*="tab"]',   # Tab elements
        '[class*="expand"]', # Expandable elements
        '[class*="accordion"]', # Accordion elements
        '[class*="pagination"]', # Pagination elements
        '[role="button"]',  # ARIA button role
        '[role="tab"]',     # ARIA tab role
        'div[class*="button"]',  # Div elements styled as buttons
        'span[class*="button"]', # Span elements styled as buttons
        'a[href="#"]',      # Links with hash href (likely JS handlers)
        'a[href="javascript:"]', # JavaScript links
    ]

    # Collect all matching elements (deduplicated)
    found_elements = set()
    for selector in selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                if element not in found_elements:
                    found_elements.add(element)

                    # Extract element information
                    text_content = element.get_text(strip=True)[:100]  # Limit to 100 chars
                    class_names = ' '.join(element.get('class', []))
                    element_html_id = element.get('id', '')
                    onclick_handler = bool(element.get('onclick'))

                    # Check if element has clickable children
                    has_children = bool(element.find_all(['button', 'a', '[onclick]'], recursive=True))

                    # Get parent tag for context
                    parent_tag = element.parent.name if element.parent else ''

                    # Get ARIA label
                    aria_label = element.get('aria-label', '') or element.get('title', '')

                    # Skip if no meaningful content and no identifying attributes
                    if not text_content and not class_names and not element_html_id and not onclick_handler and not aria_label:
                        continue

                    dynamic_element = DynamicElementInfo(
                        id=element_id,
                        tag_name=element.name,
                        text_content=text_content,
                        class_names=class_names,
                        element_id=element_html_id,
                        onclick_handler=onclick_handler,
                        has_children=has_children,
                        parent_tag=parent_tag,
                        aria_label=aria_label
                    )

                    dynamic_elements.append(dynamic_element)
                    element_id += 1
        except Exception as e:
            logging.getLogger(__name__).warning(f"Error processing selector '{selector}': {e}")
            continue

    return dynamic_elements