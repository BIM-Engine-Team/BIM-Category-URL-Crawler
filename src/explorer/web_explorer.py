import asyncio
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from models.exploration_state import ExplorationState
from models.website_node import WebsiteNode
from models.link_series import LinkSeries
from config.exploration_config import ExplorationConfig
from config.ai_config import AIConfig
from utils.http_client import HTTPClient
from explorer.page_analyzer import PageAnalyzer
from ai.exploration_ai import ExplorationAI
from ai.series_detection_ai import SeriesDetectionAI
from ai.link_relevance_ai import LinkRelevanceAI
from ai.content_classifier_ai import ContentClassifierAI

logger = logging.getLogger(__name__)


class WebExplorer:
    def __init__(self, exploration_config: ExplorationConfig, ai_config: AIConfig):
        self.config = exploration_config
        self.ai_config = ai_config
        self.page_analyzer = PageAnalyzer()
        self.state = ExplorationState()

        # AI components
        self.exploration_ai = ExplorationAI(ai_config)
        self.series_detection_ai = SeriesDetectionAI(ai_config)
        self.link_relevance_ai = LinkRelevanceAI(ai_config)
        self.content_classifier_ai = ContentClassifierAI(ai_config)

    async def explore_website(self, start_url: str) -> Dict[str, Any]:
        """
        Main exploration method that orchestrates the entire process
        """
        logger.info(f"Starting exploration of {start_url}")

        # Initialize exploration state
        self.state = ExplorationState()
        self.state.exploration_queue = [start_url]

        # Set up HTTP client and AI clients
        async with HTTPClient(self.config.request_delay) as http_client:
            async with self.exploration_ai as exp_ai, \
                      self.series_detection_ai as series_ai, \
                      self.link_relevance_ai as relevance_ai, \
                      self.content_classifier_ai as classifier_ai:

                while (self.state.exploration_queue and
                       len(self.state.visited_urls) < self.config.max_pages and
                       self.state.current_depth < self.config.max_depth):

                    current_url = self.state.exploration_queue.pop(0)

                    if current_url in self.state.visited_urls:
                        continue

                    await self._explore_page(
                        current_url,
                        http_client,
                        exp_ai,
                        series_ai,
                        relevance_ai,
                        classifier_ai
                    )

                    # Check if we should terminate exploration
                    should_stop = await exp_ai.should_terminate_exploration(
                        {
                            'current_depth': self.state.current_depth,
                            'exploration_queue': self.state.exploration_queue
                        },
                        {
                            'visited_count': len(self.state.visited_urls),
                            'max_pages': self.config.max_pages,
                            'max_depth': self.config.max_depth
                        }
                    )

                    if should_stop:
                        logger.info("AI determined exploration should terminate")
                        break

        # Return exploration results
        return self._generate_exploration_results()

    async def _explore_page(
        self,
        url: str,
        http_client: HTTPClient,
        exploration_ai: ExplorationAI,
        series_ai: SeriesDetectionAI,
        relevance_ai: LinkRelevanceAI,
        classifier_ai: ContentClassifierAI
    ):
        """
        Explore a single page and update exploration state
        """
        logger.info(f"Exploring page: {url}")

        # Fetch page content
        response = await http_client.get(url)
        if not response:
            logger.warning(f"Failed to fetch {url}")
            return

        html_content = response['content']
        self.state.visited_urls.add(url)

        # Extract page metadata and links
        metadata = self.page_analyzer.extract_page_metadata(html_content, url)
        all_links = self.page_analyzer.extract_links(html_content, url)
        classified_links = self.page_analyzer.classify_links_by_section(html_content, url)

        # Classify page content using AI
        content_classification = await classifier_ai.classify_page_content(
            url, metadata.get('text_content', ''), metadata.get('title', '')
        )

        # Create website node
        node = WebsiteNode(
            url=url,
            node_type=content_classification.get('page_type', 'other') if content_classification else 'other',
            children=[],
            exploration_status='explored',
            is_terminal=False
        )

        # Get AI exploration decisions
        exploration_decision = await exploration_ai.decide_exploration_strategy(
            url,
            metadata.get('text_content', '')[:2000],
            self.state.current_depth,
            len(self.state.visited_urls),
            {
                'page_type': node.node_type,
                'link_count': len(all_links),
                'relevance_score': content_classification.get('relevance_score', 5) if content_classification else 5
            }
        )

        if exploration_decision and exploration_decision['is_leaf_node']:
            node.is_terminal = True
            node.exploration_status = 'leaf'
            self.state.tree_nodes[url] = node
            return

        # Detect link series using AI
        priority_links = classified_links.get('navigation', []) + classified_links.get('content', [])

        if priority_links:
            series_result = await series_ai.detect_link_series(
                priority_links,
                url,
                self.config.min_series_count
            )

            # Process detected series
            for series in series_result['detected_series']:
                pattern_id = f"{url}_{series.pattern_id}"
                self.state.detected_series[pattern_id] = series

                # Add representative samples to exploration queue
                samples = await series_ai.select_representative_samples(
                    series, self.config.max_samples_per_series
                )

                for sample_url in samples:
                    if sample_url not in self.state.visited_urls:
                        self.state.exploration_queue.append(sample_url)

                # Store series reference in node
                node.link_series = series

            # Process individual links (not part of series)
            individual_links = series_result['individual_links']

            # Filter individual links by relevance
            if individual_links:
                relevance_result = await relevance_ai.filter_links_by_relevance(
                    individual_links, metadata.get('text_content', '')
                )

                if relevance_result:
                    # Add high priority links to exploration queue
                    high_priority = relevance_result.get('high_priority', [])
                    medium_priority = relevance_result.get('medium_priority', [])

                    # Limit links per page to avoid explosion
                    selected_links = (high_priority[:5] + medium_priority[:3])

                    for link in selected_links:
                        if link not in self.state.visited_urls:
                            self.state.exploration_queue.append(link)

                    node.children = selected_links

        self.state.tree_nodes[url] = node

        # Update depth for next level
        if self.state.exploration_queue:
            self.state.current_depth += 1

    def _generate_exploration_results(self) -> Dict[str, Any]:
        """
        Generate final exploration results
        """
        # Convert nodes to serializable format
        serialized_nodes = {}
        for url, node in self.state.tree_nodes.items():
            serialized_nodes[url] = {
                'url': node.url,
                'node_type': node.node_type,
                'children': node.children,
                'exploration_status': node.exploration_status,
                'is_terminal': node.is_terminal,
                'link_series': node.link_series.dict() if node.link_series else None
            }

        # Convert series to serializable format
        serialized_series = {}
        for pattern_id, series in self.state.detected_series.items():
            serialized_series[pattern_id] = series.dict()

        return {
            'exploration_summary': {
                'start_url': list(self.state.tree_nodes.keys())[0] if self.state.tree_nodes else None,
                'total_pages_visited': len(self.state.visited_urls),
                'total_nodes_created': len(self.state.tree_nodes),
                'series_detected': len(self.state.detected_series),
                'max_depth_reached': self.state.current_depth
            },
            'website_structure': {
                'nodes': serialized_nodes,
                'detected_series': serialized_series,
                'visited_urls': list(self.state.visited_urls)
            },
            'crawling_patterns': self._extract_crawling_patterns(),
            'metadata': {
                'exploration_config': self.config.dict(),
                'timestamp': asyncio.get_event_loop().time()
            }
        }

    def _extract_crawling_patterns(self) -> List[Dict[str, Any]]:
        """
        Extract URL patterns suitable for future crawling
        """
        patterns = []

        # Extract patterns from detected series
        for series in self.state.detected_series.values():
            patterns.append({
                'type': 'series',
                'pattern': series.url_pattern,
                'series_type': series.series_type,
                'sample_urls': series.sample_urls,
                'estimated_count': series.total_count
            })

        # Extract patterns from individual high-value pages
        product_pages = [
            node for node in self.state.tree_nodes.values()
            if node.node_type == 'product'
        ]

        if len(product_pages) > 1:
            # Try to identify common product URL patterns
            product_urls = [node.url for node in product_pages]
            common_pattern = self._find_common_url_pattern(product_urls)

            if common_pattern:
                patterns.append({
                    'type': 'individual',
                    'pattern': common_pattern,
                    'series_type': 'product',
                    'sample_urls': product_urls[:5],
                    'estimated_count': len(product_urls)
                })

        return patterns

    def _find_common_url_pattern(self, urls: List[str]) -> Optional[str]:
        """
        Find common pattern in a list of URLs
        """
        if not urls:
            return None

        # Simple pattern detection - look for common path structure
        parsed_urls = [urlparse(url) for url in urls]

        if all(parsed.netloc == parsed_urls[0].netloc for parsed in parsed_urls):
            # Same domain, check for path patterns
            paths = [parsed.path for parsed in parsed_urls]

            if len(set(paths)) != len(paths):
                # Some paths are duplicates
                return f"{parsed_urls[0].scheme}://{parsed_urls[0].netloc}/{{path}}"

            # Check for common path prefixes
            if len(paths) > 1:
                common_parts = []
                path_parts = [path.split('/') for path in paths]
                min_parts = min(len(parts) for parts in path_parts)

                for i in range(min_parts):
                    parts_at_position = [parts[i] for parts in path_parts]
                    if len(set(parts_at_position)) == 1:
                        common_parts.append(parts_at_position[0])
                    else:
                        break

                if common_parts:
                    base_pattern = '/'.join(common_parts)
                    return f"{parsed_urls[0].scheme}://{parsed_urls[0].netloc}/{base_pattern}/{{id}}"

        return None