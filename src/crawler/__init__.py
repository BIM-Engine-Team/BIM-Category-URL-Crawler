"""
Website Crawler Package

A utility to crawl all links from a website starting from the homepage.
Handles relative paths and controls crawling scope to stay within the same domain.
Uses breadth-first search and displays results in a tree structure.
"""

from .core import WebsiteCrawler
from .models import WebsiteNode

__version__ = "1.0.0"
__all__ = ["WebsiteCrawler", "WebsiteNode"]