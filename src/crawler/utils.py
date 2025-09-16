"""
Utility functions for the website crawler.
"""

from urllib.parse import urlparse
import logging


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