import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
from .pattern_extractor import PatternExtractor


class SchemaGenerator:
    def __init__(self):
        self.pattern_extractor = PatternExtractor()

    def generate_crawling_schema(
        self,
        exploration_results: Dict[str, Any],
        schema_name: str = "architecture_materials_schema"
    ) -> Dict[str, Any]:
        """
        Generate complete crawling schema from exploration results
        """
        # Extract patterns from exploration
        patterns = self.pattern_extractor.extract_data_patterns(exploration_results)

        # Get domain information
        summary = exploration_results.get('exploration_summary', {})
        start_url = summary.get('start_url', '')
        domain = urlparse(start_url).netloc if start_url else 'unknown'

        # Generate schema
        schema = {
            'schema_info': {
                'name': schema_name,
                'domain': domain,
                'generated_at': datetime.utcnow().isoformat(),
                'exploration_summary': summary
            },
            'crawling_configuration': self._generate_crawling_config(patterns, exploration_results),
            'url_patterns': patterns.get('url_patterns', []),
            'data_extraction': self._generate_extraction_schema(patterns),
            'pagination_handling': patterns.get('pagination_patterns', []),
            'navigation_strategy': patterns.get('navigation_patterns', {}),
            'quality_checks': self._generate_quality_checks(),
            'output_format': self._generate_output_format()
        }

        return schema

    def _generate_crawling_config(
        self,
        patterns: Dict[str, Any],
        exploration_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate crawling configuration settings
        """
        summary = exploration_results.get('exploration_summary', {})

        config = {
            'concurrent_requests': 8,
            'download_delay': 1.5,
            'randomize_download_delay': 0.5,
            'respect_robots_txt': True,
            'max_pages': min(summary.get('total_pages_visited', 100) * 5, 1000),
            'max_depth': summary.get('max_depth_reached', 4) + 1,
            'allowed_domains': [urlparse(summary.get('start_url', '')).netloc],
            'user_agent': 'ArchitectureMaterialsCrawler (+http://example.com/bot)',
            'item_pipeline': [
                'architecture_materials.pipelines.ValidationPipeline',
                'architecture_materials.pipelines.DeduplicationPipeline',
                'architecture_materials.pipelines.JsonWriterPipeline'
            ]
        }

        # Add series-specific configuration
        detected_series = exploration_results.get('website_structure', {}).get('detected_series', {})
        if detected_series:
            config['series_handling'] = {
                'max_samples_per_series': 100,
                'series_detection_enabled': True,
                'detected_series_count': len(detected_series)
            }

        return config

    def _generate_extraction_schema(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data extraction schema
        """
        field_rules = patterns.get('field_extraction_rules', {})
        data_selectors = patterns.get('data_selectors', {})

        extraction_schema = {
            'target_fields': {},
            'extraction_methods': {},
            'validation_rules': {}
        }

        # Define target fields for architecture materials
        target_fields = {
            'product_name': {
                'type': 'string',
                'required': True,
                'description': 'Product name or title'
            },
            'price': {
                'type': 'float',
                'required': False,
                'description': 'Product price in USD'
            },
            'sku': {
                'type': 'string',
                'required': False,
                'description': 'SKU or product identifier'
            },
            'category': {
                'type': 'string',
                'required': False,
                'description': 'Product category'
            },
            'description': {
                'type': 'text',
                'required': False,
                'description': 'Product description'
            },
            'specifications': {
                'type': 'object',
                'required': False,
                'description': 'Technical specifications'
            },
            'images': {
                'type': 'array',
                'required': False,
                'description': 'Product images URLs'
            },
            'dimensions': {
                'type': 'object',
                'required': False,
                'description': 'Product dimensions'
            },
            'material': {
                'type': 'string',
                'required': False,
                'description': 'Material type'
            },
            'manufacturer': {
                'type': 'string',
                'required': False,
                'description': 'Manufacturer name'
            },
            'availability': {
                'type': 'string',
                'required': False,
                'description': 'Stock availability'
            }
        }

        extraction_schema['target_fields'] = target_fields

        # Generate extraction methods for each field
        for field_name, field_config in target_fields.items():
            if field_name in data_selectors:
                extraction_schema['extraction_methods'][field_name] = {
                    'css_selectors': data_selectors[field_name],
                    'xpath_selectors': self._generate_xpath_alternatives(data_selectors[field_name]),
                    'regex_patterns': field_rules.get(field_name, {}).get('regex_patterns', []),
                    'cleaning_rules': field_rules.get(field_name, {}).get('cleaning_rules', [])
                }

        return extraction_schema

    def _generate_xpath_alternatives(self, css_selectors: List[str]) -> List[str]:
        """
        Generate XPath alternatives for CSS selectors
        """
        xpath_selectors = []

        for css_selector in css_selectors[:3]:  # Limit to first 3
            # Simple CSS to XPath conversion for common patterns
            if css_selector.startswith('.'):
                class_name = css_selector[1:]
                xpath_selectors.append(f"//*[contains(@class, '{class_name}')]")
            elif css_selector.startswith('#'):
                id_name = css_selector[1:]
                xpath_selectors.append(f"//*[@id='{id_name}']")
            elif css_selector in ['h1', 'h2', 'h3', 'p', 'span', 'div']:
                xpath_selectors.append(f"//{css_selector}")

        return xpath_selectors

    def _generate_quality_checks(self) -> Dict[str, Any]:
        """
        Generate data quality validation checks
        """
        return {
            'required_fields_check': {
                'enabled': True,
                'required_fields': ['product_name'],
                'action_on_failure': 'skip_item'
            },
            'price_validation': {
                'enabled': True,
                'min_price': 0.01,
                'max_price': 100000.00,
                'currency_check': True
            },
            'url_validation': {
                'enabled': True,
                'check_image_urls': True,
                'validate_product_links': True
            },
            'duplicate_detection': {
                'enabled': True,
                'duplicate_fields': ['sku', 'product_name'],
                'similarity_threshold': 0.9
            },
            'content_relevance': {
                'enabled': True,
                'architecture_keywords': [
                    'doors', 'windows', 'roofing', 'flooring', 'siding',
                    'tiles', 'lumber', 'hardware', 'fixtures', 'materials'
                ],
                'relevance_threshold': 0.3
            }
        }

    def _generate_output_format(self) -> Dict[str, Any]:
        """
        Generate output format specification
        """
        return {
            'format': 'json',
            'structure': 'flat',
            'file_naming': {
                'pattern': 'architecture_materials_{domain}_{timestamp}.json',
                'timestamp_format': '%Y%m%d_%H%M%S'
            },
            'batch_size': 1000,
            'compression': 'gzip',
            'include_metadata': True,
            'metadata_fields': [
                'crawl_timestamp',
                'source_url',
                'extraction_confidence',
                'data_quality_score'
            ]
        }

    def generate_scrapy_settings(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Scrapy settings based on the schema
        """
        crawling_config = schema.get('crawling_configuration', {})

        settings = {
            'BOT_NAME': 'architecture_materials_crawler',
            'SPIDER_MODULES': ['architecture_materials.spiders'],
            'NEWSPIDER_MODULE': 'architecture_materials.spiders',
            'ROBOTSTXT_OBEY': crawling_config.get('respect_robots_txt', True),
            'CONCURRENT_REQUESTS': crawling_config.get('concurrent_requests', 8),
            'CONCURRENT_REQUESTS_PER_DOMAIN': crawling_config.get('concurrent_requests', 8),
            'DOWNLOAD_DELAY': crawling_config.get('download_delay', 1.5),
            'RANDOMIZE_DOWNLOAD_DELAY': crawling_config.get('randomize_download_delay', 0.5),
            'USER_AGENT': crawling_config.get('user_agent', 'architecture_materials_crawler'),
            'DEPTH_LIMIT': crawling_config.get('max_depth', 5),
            'CLOSESPIDER_PAGECOUNT': crawling_config.get('max_pages', 1000),

            'ITEM_PIPELINES': {
                'architecture_materials.pipelines.ValidationPipeline': 300,
                'architecture_materials.pipelines.DeduplicationPipeline': 400,
                'architecture_materials.pipelines.JsonWriterPipeline': 500,
            },

            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 1,
            'AUTOTHROTTLE_MAX_DELAY': 60,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
            'AUTOTHROTTLE_DEBUG': False,

            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_EXPIRATION_SECS': 3600,

            'DEFAULT_REQUEST_HEADERS': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en',
            }
        }

        return settings

    def export_schema(
        self,
        schema: Dict[str, Any],
        output_path: str,
        format: str = 'json'
    ) -> bool:
        """
        Export schema to file
        """
        try:
            if format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                return True
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            print(f"Error exporting schema: {e}")
            return False

    def validate_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the generated schema
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check required sections
        required_sections = [
            'schema_info', 'crawling_configuration', 'data_extraction'
        ]

        for section in required_sections:
            if section not in schema:
                validation_result['errors'].append(f"Missing required section: {section}")
                validation_result['is_valid'] = False

        # Check data extraction fields
        data_extraction = schema.get('data_extraction', {})
        target_fields = data_extraction.get('target_fields', {})

        if not target_fields:
            validation_result['errors'].append("No target fields defined for data extraction")
            validation_result['is_valid'] = False

        if 'product_name' not in target_fields:
            validation_result['warnings'].append("Product name field not defined - this is typically required")

        # Check URL patterns
        url_patterns = schema.get('url_patterns', [])
        if not url_patterns:
            validation_result['warnings'].append("No URL patterns detected - crawling may be inefficient")

        # Recommendations
        if len(target_fields) < 5:
            validation_result['recommendations'].append("Consider adding more target fields for richer data extraction")

        crawling_config = schema.get('crawling_configuration', {})
        if crawling_config.get('concurrent_requests', 1) > 16:
            validation_result['recommendations'].append("High concurrency may cause rate limiting - consider reducing")

        return validation_result