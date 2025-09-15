import re
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urlparse, parse_qs
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class PatternExtractor:
    def __init__(self):
        self.common_selectors = {
            'product_name': [
                'h1', '.product-title', '.product-name', '[data-product-name]',
                '.title', '#product-title', '.name'
            ],
            'price': [
                '.price', '.cost', '.amount', '[data-price]', '.product-price',
                '.price-current', '.regular-price', '.sale-price'
            ],
            'description': [
                '.description', '.product-description', '.details', '.summary',
                '.product-details', '[data-description]'
            ],
            'images': [
                '.product-image img', '.gallery img', '.photos img',
                '.product-photos img', '[data-product-image]'
            ],
            'specifications': [
                '.specs', '.specifications', '.features', '.attributes',
                '.product-specs', '.technical-details'
            ],
            'category': [
                '.breadcrumb', '.category', '.product-category', '.navigation',
                '[data-category]', '.category-path'
            ],
            'sku': [
                '.sku', '.product-id', '.model-number', '[data-sku]',
                '.part-number', '.product-code'
            ]
        }

    def extract_data_patterns(self, exploration_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data extraction patterns from exploration results
        """
        website_structure = exploration_results.get('website_structure', {})
        nodes = website_structure.get('nodes', {})

        patterns = {
            'url_patterns': self._extract_url_patterns(nodes),
            'data_selectors': self._generate_data_selectors(nodes),
            'pagination_patterns': self._extract_pagination_patterns(website_structure),
            'navigation_patterns': self._extract_navigation_patterns(nodes),
            'field_extraction_rules': self._create_field_extraction_rules()
        }

        return patterns

    def _extract_url_patterns(self, nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract URL patterns for different page types
        """
        patterns = []
        pages_by_type = defaultdict(list)

        # Group pages by type
        for url, node in nodes.items():
            page_type = node.get('node_type', 'other')
            pages_by_type[page_type].append(url)

        # Generate patterns for each page type
        for page_type, urls in pages_by_type.items():
            if len(urls) > 1:
                pattern = self._find_url_pattern(urls)
                if pattern:
                    patterns.append({
                        'page_type': page_type,
                        'url_pattern': pattern,
                        'sample_urls': urls[:5],
                        'count': len(urls)
                    })

        return patterns

    def _find_url_pattern(self, urls: List[str]) -> Optional[str]:
        """
        Find common pattern in URLs
        """
        if len(urls) < 2:
            return None

        # Parse all URLs
        parsed_urls = [urlparse(url) for url in urls]
        base_url = f"{parsed_urls[0].scheme}://{parsed_urls[0].netloc}"

        # Find common path structure
        paths = [parsed.path for parsed in parsed_urls]
        path_parts = [path.strip('/').split('/') for path in paths]

        if not path_parts:
            return base_url

        min_parts = min(len(parts) for parts in path_parts)
        common_parts = []

        for i in range(min_parts):
            parts_at_position = [parts[i] for parts in path_parts if len(parts) > i]
            unique_parts = set(parts_at_position)

            if len(unique_parts) == 1:
                common_parts.append(parts_at_position[0])
            else:
                # Check if parts look like IDs or parameters
                if self._looks_like_variable_part(unique_parts):
                    common_parts.append('{id}')
                else:
                    break

        if common_parts:
            pattern = base_url + '/' + '/'.join(common_parts)
            return pattern

        return None

    def _looks_like_variable_part(self, parts: Set[str]) -> bool:
        """
        Check if URL parts look like variable identifiers
        """
        if len(parts) < 2:
            return False

        # Check if all parts are numeric
        numeric_count = sum(1 for part in parts if part.isdigit())
        if numeric_count == len(parts):
            return True

        # Check if parts look like product codes/SKUs
        alphanumeric_pattern = re.compile(r'^[a-zA-Z0-9\-_]+$')
        matching_count = sum(1 for part in parts if alphanumeric_pattern.match(part))

        return matching_count == len(parts)

    def _generate_data_selectors(self, nodes: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate CSS selectors for data extraction based on common patterns
        """
        selectors = {}

        # Start with common selector patterns
        for field, patterns in self.common_selectors.items():
            selectors[field] = patterns.copy()

        # Analyze product pages to refine selectors
        product_nodes = [
            node for node in nodes.values()
            if node.get('node_type') == 'product'
        ]

        if len(product_nodes) > 2:
            # Could analyze actual page content here to find more specific selectors
            # For now, return the common patterns
            pass

        return selectors

    def _extract_pagination_patterns(self, website_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract pagination patterns from detected series
        """
        pagination_patterns = []
        detected_series = website_structure.get('detected_series', {})

        for series_id, series_data in detected_series.items():
            if series_data.get('series_type') == 'pagination':
                pattern = {
                    'type': 'pagination',
                    'url_pattern': series_data.get('url_pattern'),
                    'parameter_pattern': self._extract_pagination_parameter(
                        series_data.get('sample_urls', [])
                    ),
                    'estimated_pages': series_data.get('total_count', 1)
                }
                pagination_patterns.append(pattern)

        return pagination_patterns

    def _extract_pagination_parameter(self, urls: List[str]) -> Dict[str, Any]:
        """
        Extract pagination parameter pattern from URLs
        """
        if not urls:
            return {}

        # Parse query parameters
        param_names = set()
        param_values = []

        for url in urls:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            for param_name, values in query_params.items():
                if values and values[0].isdigit():
                    param_names.add(param_name)
                    param_values.extend([int(v) for v in values if v.isdigit()])

        if param_names and param_values:
            likely_param = list(param_names)[0]  # Take first pagination parameter
            return {
                'parameter_name': likely_param,
                'start_value': min(param_values),
                'max_value': max(param_values),
                'increment': 1  # Assume increment of 1
            }

        return {}

    def _extract_navigation_patterns(self, nodes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract navigation patterns for systematic crawling
        """
        navigation_patterns = {
            'category_hierarchy': [],
            'breadcrumb_patterns': [],
            'menu_structures': []
        }

        # Analyze nodes to identify navigation patterns
        category_nodes = [
            node for node in nodes.values()
            if node.get('node_type') == 'category'
        ]

        if category_nodes:
            # Extract category hierarchy
            for node in category_nodes:
                children = node.get('children', [])
                if children:
                    navigation_patterns['category_hierarchy'].append({
                        'parent_url': node['url'],
                        'child_urls': children[:10],  # Limit for brevity
                        'estimated_subcategories': len(children)
                    })

        return navigation_patterns

    def _create_field_extraction_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Create field-specific extraction rules
        """
        rules = {}

        # Price extraction rules
        rules['price'] = {
            'selectors': self.common_selectors['price'],
            'regex_patterns': [
                r'\$[\d,]+\.?\d*',
                r'USD\s*[\d,]+\.?\d*',
                r'Price:\s*\$?[\d,]+\.?\d*'
            ],
            'cleaning_rules': [
                'remove_currency_symbols',
                'convert_to_float',
                'handle_ranges'
            ]
        }

        # SKU/Product ID extraction rules
        rules['sku'] = {
            'selectors': self.common_selectors['sku'],
            'regex_patterns': [
                r'SKU[:\s]+([A-Z0-9\-]+)',
                r'Model[:\s]+([A-Z0-9\-]+)',
                r'Part[:\s]*#[:\s]*([A-Z0-9\-]+)'
            ],
            'cleaning_rules': [
                'extract_alphanumeric',
                'uppercase'
            ]
        }

        # Product name extraction rules
        rules['product_name'] = {
            'selectors': self.common_selectors['product_name'],
            'regex_patterns': [],
            'cleaning_rules': [
                'trim_whitespace',
                'remove_extra_spaces'
            ]
        }

        # Description extraction rules
        rules['description'] = {
            'selectors': self.common_selectors['description'],
            'regex_patterns': [],
            'cleaning_rules': [
                'trim_whitespace',
                'remove_html_tags',
                'normalize_line_breaks'
            ]
        }

        return rules

    def generate_scrapy_spider_template(
        self,
        patterns: Dict[str, Any],
        spider_name: str,
        domain: str
    ) -> str:
        """
        Generate a Scrapy spider template based on extracted patterns
        """
        template = f"""
import scrapy
from urllib.parse import urljoin


class {spider_name.title()}Spider(scrapy.Spider):
    name = '{spider_name}'
    allowed_domains = ['{domain}']

    def start_requests(self):
        # Generated start URLs based on exploration
        start_urls = {self._get_start_urls(patterns)}

        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Extract data based on identified patterns
        {self._generate_extraction_code(patterns)}

        # Follow pagination if detected
        {self._generate_pagination_code(patterns)}

        # Follow category links
        {self._generate_navigation_code(patterns)}
"""

        return template

    def _get_start_urls(self, patterns: Dict[str, Any]) -> List[str]:
        """
        Get start URLs from patterns
        """
        url_patterns = patterns.get('url_patterns', [])
        start_urls = []

        for pattern in url_patterns:
            if pattern.get('page_type') in ['homepage', 'category']:
                start_urls.extend(pattern.get('sample_urls', [])[:3])

        return start_urls[:10]  # Limit start URLs

    def _generate_extraction_code(self, patterns: Dict[str, Any]) -> str:
        """
        Generate data extraction code
        """
        field_rules = patterns.get('field_extraction_rules', {})
        code_lines = []

        for field, rules in field_rules.items():
            selectors = rules.get('selectors', [])
            if selectors:
                selector_str = "', '".join(selectors[:3])
                code_lines.append(f"        {field} = response.css('{selector_str}').get()")

        return '\n'.join(code_lines) if code_lines else "        # Add extraction logic here"

    def _generate_pagination_code(self, patterns: Dict[str, Any]) -> str:
        """
        Generate pagination handling code
        """
        pagination_patterns = patterns.get('pagination_patterns', [])

        if pagination_patterns:
            return """        # Handle pagination
        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)"""

        return "        # No pagination patterns detected"

    def _generate_navigation_code(self, patterns: Dict[str, Any]) -> str:
        """
        Generate navigation following code
        """
        return """        # Follow category and product links
        category_links = response.css('.category-link::attr(href)').getall()
        for link in category_links:
            yield response.follow(link, callback=self.parse)

        product_links = response.css('.product-link::attr(href)').getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product)"""