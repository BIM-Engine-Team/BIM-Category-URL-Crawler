from typing import Set, Dict, List
from pydantic import BaseModel
from models.website_node import WebsiteNode
from models.link_series import LinkSeries


class ExplorationState(BaseModel):
    visited_urls: Set[str] = set()
    tree_nodes: Dict[str, WebsiteNode] = {}
    detected_series: Dict[str, LinkSeries] = {}
    exploration_queue: List[str] = []
    current_depth: int = 0

    class Config:
        # Allow sets in Pydantic v2
        arbitrary_types_allowed = True