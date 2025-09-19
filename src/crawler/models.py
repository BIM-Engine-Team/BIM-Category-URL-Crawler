"""
Data models for the website crawler.
"""

from typing import Dict, Optional, List
import heapq
from dataclasses import dataclass


@dataclass
class LinkInfo:
    """Information about a link extracted from a page."""
    url: str
    relative_path: str
    title: str
    description: str
    id: int  # Index of the link for matching with AI scores
    link_tag: str  # The HTML link tag content
    link_text: str  # The visible text content of the link


@dataclass
class DynamicElementInfo:
    """Information about a potentially dynamic element extracted from a page."""
    id: int  # Index of the element for matching with AI scores
    tag_name: str  # HTML tag name (button, div, span, etc.)
    text_content: str  # Visible text content (truncated to avoid long text)
    class_names: str  # CSS class names
    element_id: str  # HTML id attribute
    onclick_handler: bool  # Whether element has click handler
    has_children: bool  # Whether element has clickable children
    parent_tag: str  # Parent element tag name for context
    aria_label: str  # ARIA label if present


class WebsiteNode:
    """Represents a node in the website tree structure with AI scoring."""

    def __init__(self, url: str, path: str = "", parent: Optional['WebsiteNode'] = None):
        self.url = url
        self.path = path  # Relative path from base URL
        self.parent = parent
        self.children: Dict[str, 'WebsiteNode'] = {}  # path -> node
        self.is_explored = False
        self.depth = 0 if parent is None else parent.depth + 1
        self.score: float = 0.0  # AI score for this node
        self.product_name: Optional[str] = None  # Set if this is a product page

    @property
    def total_children(self) -> int:
        """Total number of child nodes."""
        return len(self.children)

    @property
    def explored_children(self) -> int:
        """Number of explored child nodes."""
        return sum(1 for child in self.children.values() if child.is_explored)

    def add_child(self, url: str, path: str) -> 'WebsiteNode':
        """Add a child node if it doesn't exist."""
        if path not in self.children:
            self.children[path] = WebsiteNode(url, path, self)
        return self.children[path]

    def get_tree_display(self, prefix: str = "", is_last: bool = True) -> str:
        """Generate tree-like display string for this node and its children."""
        lines = []

        # Current node display
        connector = "└── " if is_last else "├── "
        display_path = self.path if self.path else "(root)"
        status = "✓" if self.is_explored else "○"
        stats = f"[{self.explored_children}/{self.total_children} explored]"

        lines.append(f"{prefix}{connector}{status} {display_path} {stats}")

        # Children display
        children_list = sorted(self.children.items())
        for i, (path, child) in enumerate(children_list):
            child_is_last = (i == len(children_list) - 1)
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(child.get_tree_display(child_prefix, child_is_last).split('\n'))

        return '\n'.join(lines)

    def get_average_score(self) -> float:
        """Calculate average score of this node and all ancestors."""
        scores = []
        current = self
        while current is not None:
            if current.score > 0:  # Only count nodes that have been scored
                scores.append(current.score)
            current = current.parent

        return sum(scores) / len(scores) if scores else 0.0


class OpenSet:
    """Max binary heap for prioritizing nodes to explore based on average scores."""

    def __init__(self):
        self._heap: List[tuple] = []  # (negative_avg_score, counter, node)
        self._counter = 0  # To ensure stable sorting for equal scores
        self._node_set = set()  # To track which nodes are in the heap

    def add(self, node: WebsiteNode):
        """Add a node to the open set."""
        if node not in self._node_set:
            # Use negative score for max heap behavior (Python heapq is min heap)
            avg_score = node.get_average_score()
            heapq.heappush(self._heap, (-avg_score, self._counter, node))
            self._counter += 1
            self._node_set.add(node)

    def pop(self) -> Optional[WebsiteNode]:
        """Remove and return the node with highest average score."""
        while self._heap:
            neg_score, counter, node = heapq.heappop(self._heap)
            if node in self._node_set:
                self._node_set.remove(node)
                return node
        return None

    def is_empty(self) -> bool:
        """Check if the open set is empty."""
        return len(self._node_set) == 0

    def size(self) -> int:
        """Get the number of nodes in the open set."""
        return len(self._node_set)