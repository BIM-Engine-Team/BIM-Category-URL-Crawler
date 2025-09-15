from typing import List, Dict, Any, Optional
from ai.base_ai_client import BaseAIClient
from ai.prompt_templates import PromptTemplates
from config.ai_config import AIConfig
from models.link_series import LinkSeries


class SeriesDetectionAI:
    def __init__(self, config: AIConfig):
        self.client = BaseAIClient(config)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def detect_link_series(
        self,
        links: List[str],
        base_url: str,
        min_series_count: int = 3
    ) -> Dict[str, Any]:
        """
        Identifies link patterns and groups similar URLs into series
        Returns detected series and individual links
        """
        if len(links) < min_series_count:
            return {
                'detected_series': [],
                'individual_links': links,
                'reasoning': 'Not enough links to form series'
            }

        prompt = PromptTemplates.series_detection(links, base_url)
        result = await self.client.query(prompt)

        if result and 'detected_series' in result:
            # Convert to LinkSeries objects
            series_objects = []
            for series_data in result['detected_series']:
                try:
                    link_series = LinkSeries(
                        pattern_id=series_data['pattern_id'],
                        url_pattern=series_data['url_pattern'],
                        sample_urls=series_data['sample_urls'],
                        total_count=series_data['total_count'],
                        series_type=series_data['series_type']
                    )
                    series_objects.append(link_series)
                except Exception as e:
                    print(f"Error creating LinkSeries: {e}")
                    continue

            return {
                'detected_series': series_objects,
                'individual_links': result.get('individual_links', []),
                'reasoning': result.get('reasoning', '')
            }

        # Fallback: treat all links as individual
        return {
            'detected_series': [],
            'individual_links': links,
            'reasoning': 'AI detection failed, treating as individual links'
        }

    async def select_representative_samples(
        self,
        series: LinkSeries,
        max_samples: int = 5
    ) -> List[str]:
        """
        Selects diverse, representative samples from a link series
        """
        if len(series.sample_urls) <= max_samples:
            return series.sample_urls

        # For now, return evenly distributed samples
        # Could be enhanced with AI-based selection
        step = len(series.sample_urls) // max_samples
        return [
            series.sample_urls[i * step]
            for i in range(max_samples)
        ]

    async def classify_series_type(
        self,
        url_pattern: str,
        sample_urls: List[str]
    ) -> str:
        """
        Classifies the type of link series (pagination, category, product_variant)
        """
        # Simple pattern matching for now
        pattern_lower = url_pattern.lower()

        if any(keyword in pattern_lower for keyword in ['page', 'offset', 'start']):
            return 'pagination'
        elif any(keyword in pattern_lower for keyword in ['category', 'cat', 'section']):
            return 'category'
        elif any(keyword in pattern_lower for keyword in ['product', 'item', 'id']):
            return 'product_variant'
        else:
            return 'unknown'

    def estimate_series_total(
        self,
        sample_urls: List[str],
        pattern: str
    ) -> int:
        """
        Estimates total count in a series based on samples and pattern
        """
        # Extract numbers from URLs to estimate range
        import re
        numbers = []

        for url in sample_urls:
            found_numbers = re.findall(r'\d+', url)
            if found_numbers:
                numbers.extend([int(n) for n in found_numbers])

        if numbers:
            return max(numbers) - min(numbers) + 1
        else:
            # Fallback estimate
            return len(sample_urls) * 10