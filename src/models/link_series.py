from typing import List
from pydantic import BaseModel


class LinkSeries(BaseModel):
    pattern_id: str
    url_pattern: str  # e.g., "/products?page={num}"
    sample_urls: List[str]  # 3-5 representative samples
    total_count: int
    series_type: str  # 'pagination', 'category', 'product_variant'