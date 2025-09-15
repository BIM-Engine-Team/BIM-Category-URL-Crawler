from pydantic import BaseModel
from typing import List


class ExplorationConfig(BaseModel):
    max_depth: int = 4
    max_pages: int = 200
    min_series_count: int = 3
    max_samples_per_series: int = 5
    request_delay: float = 1.5  # seconds between requests

    # Content focus
    architecture_keywords: List[str] = [
        "doors", "windows", "roofing", "flooring", "siding", "tiles",
        "lumber", "hardware", "fixtures", "materials", "construction",
        "building", "architectural", "commercial", "residential"
    ]

    skip_patterns: List[str] = [
        "contact", "about", "legal", "privacy", "terms", "login",
        "register", "account", "cart", "checkout", "support"
    ]

    prioritize_patterns: List[str] = [
        "products", "catalog", "categories", "specifications",
        "materials", "gallery", "portfolio"
    ]