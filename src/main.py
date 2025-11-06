"""
Main entry point for the AI-guided web crawler.
"""

import argparse
import json
import logging
import os
from typing import List, Dict

from src.crawler.ai_crawler import AIGuidedCrawler
from src.util.result_cleaner import clean_crawler_results


def load_task_config(config_path: str) -> Dict:
    """Load task configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Task config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")


def main():
    """Main function to run the AI-guided crawler."""
    parser = argparse.ArgumentParser(description='AI-guided web crawler for product discovery')
    parser.add_argument('config', help='Path to task configuration file (JSON format)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Load task configuration
        logger.info(f"Loading task configuration from: {args.config}")
        config = load_task_config(args.config)

        # Extract parameters from config
        base_url = config.get('url')
        if not base_url:
            raise ValueError("Missing required 'url' in task configuration")

        delay = config.get('delay', 1.0)
        max_pages = config.get('max_pages', 50)
        output_file = config.get('output')
        enable_dynamic_loading = config.get('enable_dynamic_loading', False)

        # Extract AI configuration from task config if present
        ai_provider = config.get('ai_provider')
        ai_model = config.get('ai_model')

        logger.info(f"Configuration loaded:")
        logger.info(f"  URL: {base_url}")
        logger.info(f"  Delay: {delay}s")
        logger.info(f"  Max pages: {max_pages}")
        logger.info(f"  Dynamic loading: {'enabled' if enable_dynamic_loading else 'disabled'}")
        logger.info(f"  Output file: {output_file or 'auto-generated'}")
        if ai_provider or ai_model:
            logger.info(f"  AI Provider: {ai_provider or 'default'}")
            logger.info(f"  AI Model: {ai_model or 'default'}")

        # Initialize crawler
        logger.info(f"Initializing AI-guided crawler for: {base_url}")
        crawler = AIGuidedCrawler(
            base_url=base_url,
            delay=delay,
            max_pages=max_pages,
            ai_provider=ai_provider,
            ai_model=ai_model,
            enable_dynamic_loading=enable_dynamic_loading
        )

        # Start crawling
        products = crawler.crawl()

        # Display results
        logger.info(f"Crawling completed! Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['productName']}")
            print(f"   URL: {product['url']}")
            print()

        # Save raw results first
        if output_file:
            # Generate raw filename by adding _raw before extension
            from pathlib import Path
            output_path = Path(output_file)
            raw_output_file = str(output_path.parent / f"{output_path.stem}_raw{output_path.suffix}")
            final_output_file = output_file
        else:
            # Use default filenames
            raw_output_file = f"ai_crawl_results_{crawler.domain.replace('.', '_')}_raw.json"
            final_output_file = f"ai_crawl_results_{crawler.domain.replace('.', '_')}.json"

        # Save raw results
        logger.info(f"Saving raw results to: {raw_output_file}")
        crawler.save_results(raw_output_file)

        # Clean duplicates from results (this is a necessary step)
        logger.info("Cleaning duplicate products from results...")
        try:
            cleaned_file = clean_crawler_results(raw_output_file, final_output_file)
            logger.info(f"✓ Duplicate cleaning completed. Final results saved to: {cleaned_file}")
        except Exception as e:
            logger.error(f"✗ Failed to clean duplicates: {e}")
            logger.info("This is a critical step - crawling process incomplete")
            return 1

        # Print summary
        results = crawler.get_results()
        print(f"Summary:")
        print(f"  Products found: {len(results['products'])}")
        print(f"  Pages processed: {results['pages_processed']}")
        print(f"  Total nodes discovered: {results['total_nodes']}")
        print(f"  Raw results: {raw_output_file}")
        print(f"  Final results: {final_output_file}")

    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())