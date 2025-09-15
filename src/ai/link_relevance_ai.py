from typing import List, Dict, Any, Optional
from ai.base_ai_client import BaseAIClient
from ai.prompt_templates import PromptTemplates
from config.ai_config import AIConfig


class LinkRelevanceAI:
    def __init__(self, config: AIConfig):
        self.client = BaseAIClient(config)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def filter_links_by_relevance(
        self,
        links: List[str],
        page_context: str
    ) -> Optional[Dict[str, Any]]:
        """
        Filters links based on architecture material relevance
        Returns categorized links by priority level
        """
        if not links:
            return {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'skip': [],
                'reasoning': 'No links provided'
            }

        prompt = PromptTemplates.link_relevance(links, page_context)
        result = await self.client.query(prompt)

        if result and 'high_priority' in result:
            return {
                'high_priority': result.get('high_priority', []),
                'medium_priority': result.get('medium_priority', []),
                'low_priority': result.get('low_priority', []),
                'skip': result.get('skip', []),
                'reasoning': result.get('reasoning', '')
            }

        # Fallback: basic keyword filtering
        return self._fallback_filter(links, page_context)

    def _fallback_filter(
        self,
        links: List[str],
        page_context: str
    ) -> Dict[str, Any]:
        """
        Fallback link filtering using simple keyword matching
        """
        high_keywords = [
            'product', 'catalog', 'category', 'materials', 'doors',
            'windows', 'roofing', 'flooring', 'siding', 'tiles'
        ]

        skip_keywords = [
            'contact', 'about', 'login', 'register', 'cart',
            'checkout', 'privacy', 'terms', 'legal'
        ]

        high_priority = []
        medium_priority = []
        low_priority = []
        skip = []

        for link in links:
            link_lower = link.lower()

            if any(keyword in link_lower for keyword in skip_keywords):
                skip.append(link)
            elif any(keyword in link_lower for keyword in high_keywords):
                high_priority.append(link)
            elif any(keyword in link_lower for keyword in ['specs', 'info', 'details']):
                medium_priority.append(link)
            else:
                low_priority.append(link)

        return {
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'skip': skip,
            'reasoning': 'Fallback keyword-based filtering applied'
        }

    async def score_link_importance(
        self,
        url: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Scores individual link importance for exploration priority
        Returns score between 0.0 and 1.0
        """
        # Simple scoring based on URL patterns
        score = 0.5  # Base score

        url_lower = url.lower()

        # Boost for architecture-related keywords
        arch_keywords = [
            'product', 'catalog', 'materials', 'doors', 'windows',
            'roofing', 'flooring', 'siding', 'tiles', 'lumber'
        ]
        for keyword in arch_keywords:
            if keyword in url_lower:
                score += 0.1

        # Penalty for non-relevant sections
        skip_keywords = [
            'contact', 'about', 'login', 'cart', 'privacy', 'terms'
        ]
        for keyword in skip_keywords:
            if keyword in url_lower:
                score -= 0.3

        return max(0.0, min(1.0, score))

    def is_relevant_section(self, url: str, content_snippet: str = "") -> bool:
        """
        Quick check if a section/URL is relevant for architecture materials
        """
        combined_text = (url + " " + content_snippet).lower()

        # Check for architecture keywords
        relevant_keywords = [
            'product', 'catalog', 'materials', 'construction', 'building',
            'doors', 'windows', 'roofing', 'flooring', 'siding', 'tiles',
            'lumber', 'hardware', 'fixtures'
        ]

        irrelevant_keywords = [
            'contact', 'about', 'login', 'register', 'account',
            'cart', 'checkout', 'privacy', 'terms', 'legal', 'support'
        ]

        # Strong negative indicators
        if any(keyword in combined_text for keyword in irrelevant_keywords):
            return False

        # Positive indicators
        if any(keyword in combined_text for keyword in relevant_keywords):
            return True

        # Neutral - could be relevant
        return True