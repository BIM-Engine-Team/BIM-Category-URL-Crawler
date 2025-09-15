from typing import Dict, Any, Optional
from ai.base_ai_client import BaseAIClient
from ai.prompt_templates import PromptTemplates
from config.ai_config import AIConfig


class ContentClassifierAI:
    def __init__(self, config: AIConfig):
        self.client = BaseAIClient(config)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def classify_page_content(
        self,
        url: str,
        content: str,
        title: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Classifies page type and extracts key metadata for schema generation
        """
        prompt = PromptTemplates.content_classification(url, content, title)
        result = await self.client.query(prompt)

        if result and 'page_type' in result:
            return {
                'page_type': result.get('page_type', 'other'),
                'relevance_score': result.get('relevance_score', 5),
                'is_architecture_related': result.get('is_architecture_related', False),
                'key_metadata': result.get('key_metadata', {}),
                'extracted_info': result.get('extracted_info', {}),
                'reasoning': result.get('reasoning', '')
            }

        # Fallback classification
        return self._fallback_classification(url, content, title)

    def _fallback_classification(
        self,
        url: str,
        content: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Fallback page classification using simple heuristics
        """
        url_lower = url.lower()
        content_lower = content.lower()
        title_lower = title.lower()

        combined_text = f"{url_lower} {content_lower} {title_lower}"

        # Determine page type
        page_type = 'other'
        if any(indicator in url_lower for indicator in ['/', 'home', 'index']):
            if len(url.split('/')) <= 3:
                page_type = 'homepage'

        if any(indicator in combined_text for indicator in ['category', 'categories']):
            page_type = 'category'
        elif any(indicator in combined_text for indicator in ['product']):
            if 'products' in combined_text or 'catalog' in combined_text:
                page_type = 'listing'
            else:
                page_type = 'product'

        # Determine relevance
        arch_keywords = [
            'doors', 'windows', 'roofing', 'flooring', 'siding',
            'materials', 'construction', 'building', 'architecture'
        ]
        relevance_score = 5
        is_architecture_related = False

        arch_matches = sum(1 for keyword in arch_keywords if keyword in combined_text)
        if arch_matches > 0:
            is_architecture_related = True
            relevance_score = min(10, 5 + arch_matches)

        return {
            'page_type': page_type,
            'relevance_score': relevance_score,
            'is_architecture_related': is_architecture_related,
            'key_metadata': {
                'has_products': 'product' in combined_text,
                'has_categories': 'category' in combined_text or 'categories' in combined_text,
                'has_specifications': 'spec' in combined_text or 'specification' in combined_text,
                'navigation_depth': len(url.split('/')) - 2
            },
            'extracted_info': {
                'product_count': None,
                'category_names': [],
                'key_features': []
            },
            'reasoning': 'Fallback heuristic-based classification'
        }

    def determine_content_relevance(
        self,
        content: str,
        focus_keywords: list
    ) -> float:
        """
        Determines content relevance score based on focus keywords
        Returns score between 0.0 and 1.0
        """
        if not content or not focus_keywords:
            return 0.0

        content_lower = content.lower()
        matches = sum(1 for keyword in focus_keywords if keyword in content_lower)

        if matches == 0:
            return 0.0

        # Normalize by content length and keyword count
        content_words = len(content.split())
        keyword_density = matches / len(focus_keywords)
        content_factor = min(1.0, content_words / 500)  # Normalize for content length

        return min(1.0, keyword_density * content_factor)

    def extract_navigation_structure(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Extracts navigation structure information from page content
        """
        # Simple extraction - could be enhanced with HTML parsing
        nav_indicators = ['nav', 'menu', 'navigation', 'breadcrumb']
        has_navigation = any(indicator in content.lower() for indicator in nav_indicators)

        return {
            'has_navigation': has_navigation,
            'estimated_nav_depth': content.lower().count('›') + content.lower().count('>'),
            'navigation_keywords': [
                indicator for indicator in nav_indicators
                if indicator in content.lower()
            ]
        }