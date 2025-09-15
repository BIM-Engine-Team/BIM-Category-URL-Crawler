from typing import List, Dict, Any, Optional
from ai.base_ai_client import BaseAIClient
from ai.prompt_templates import PromptTemplates
from config.ai_config import AIConfig


class ExplorationAI:
    def __init__(self, config: AIConfig):
        self.client = BaseAIClient(config)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def decide_exploration_strategy(
        self,
        page_url: str,
        page_content: str,
        current_depth: int,
        visited_count: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determines which links to explore next based on page context
        Returns exploration decisions including priority links and leaf node status
        """
        if context is None:
            context = {}

        prompt = PromptTemplates.exploration_decision(
            page_url, page_content, current_depth, visited_count, context
        )

        result = await self.client.query(prompt)
        if result and 'priority_links' in result:
            return {
                'priority_links': result.get('priority_links', []),
                'is_leaf_node': result.get('is_leaf_node', False),
                'page_type': result.get('page_type', 'other'),
                'relevance_score': result.get('relevance_score', 5),
                'reasoning': result.get('reasoning', '')
            }

        return None

    async def should_terminate_exploration(
        self,
        current_state: Dict[str, Any],
        exploration_stats: Dict[str, Any]
    ) -> bool:
        """
        Decides whether to stop exploration based on current state
        """
        # Simple heuristics for now, can be enhanced with AI decision later
        max_pages = exploration_stats.get('max_pages', 200)
        max_depth = exploration_stats.get('max_depth', 4)

        if exploration_stats.get('visited_count', 0) >= max_pages:
            return True

        if current_state.get('current_depth', 0) >= max_depth:
            return True

        # Check if queue is empty
        if not current_state.get('exploration_queue', []):
            return True

        return False

    async def prioritize_links(
        self,
        links: List[str],
        page_context: str,
        current_depth: int
    ) -> List[str]:
        """
        Prioritizes links for exploration based on relevance and context
        """
        if not links:
            return []

        # Use link relevance AI for detailed filtering
        from .link_relevance_ai import LinkRelevanceAI
        relevance_ai = LinkRelevanceAI(self.client.config)

        async with relevance_ai:
            relevance_result = await relevance_ai.filter_links_by_relevance(
                links, page_context
            )

        if relevance_result:
            # Combine high and medium priority links
            prioritized = (
                relevance_result.get('high_priority', []) +
                relevance_result.get('medium_priority', [])
            )
            return prioritized[:10]  # Limit to top 10

        return links[:10]  # Fallback to first 10 links