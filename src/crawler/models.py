"""
Data models for the website crawler.
"""

from typing import Dict, Optional


class WebsiteNode:
    """Represents a node in the website tree structure."""

    def __init__(self, url: str, path: str = "", parent: Optional['WebsiteNode'] = None):
        self.url = url
        self.path = path  # Relative path from base URL
        self.parent = parent
        self.children: Dict[str, 'WebsiteNode'] = {}  # path -> node
        self.is_explored = False
        self.depth = 0 if parent is None else parent.depth + 1

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