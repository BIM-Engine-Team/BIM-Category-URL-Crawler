from typing import List, Optional
from pydantic import BaseModel
from models.link_series import LinkSeries


class WebsiteNode(BaseModel):
    url: str
    node_type: str  # 'homepage', 'category', 'product', 'listing'
    children: List[str]
    link_series: Optional[LinkSeries] = None
    exploration_status: str  # 'explored', 'skipped', 'series_sample', 'leaf'
    is_terminal: bool  # Claude-determined leaf node status