#!/usr/bin/env python3
"""
Website Structure Exploration System
Main entry point for the architecture materials website exploration system.
"""

import asyncio
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Optional

from config.exploration_config import ExplorationConfig
from config.ai_config import AIConfig
from config.env_config import get_env_config
from explorer.web_explorer import WebExplorer
from schema.schema_generator import SchemaGenerator


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('exploration.log')
        ]
    )


async def explore_website(
    url: str,
    output_dir: str = "output",
    config_file: Optional[str] = None
) -> bool:
    """
    Main exploration function
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting exploration of {url}")

    try:
        # Load environment configuration
        env_config = get_env_config()

        # Validate environment variables
        env_validation = env_config.validate_required_keys()
        if not env_validation['valid']:
            logger.error("Environment configuration errors:")
            for error in env_validation['errors']:
                logger.error(f"  - {error}")
            logger.error("\nPlease check your .env file or environment variables")
            return False

        # Show warnings if any
        for warning in env_validation['warnings']:
            logger.warning(warning)

        # Load configurations
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                exploration_config = ExplorationConfig(**config_data.get('exploration', {}))
                ai_config = AIConfig(**config_data.get('ai', {}))
        else:
            exploration_config = ExplorationConfig()
            ai_config = AIConfig()

        # Validate AI configuration
        try:
            ai_config.validate_config()
        except ValueError as e:
            logger.error(f"AI configuration error: {e}")
            logger.error("Please check your .env file and ensure CLAUDE_API_KEY is set")
            return False

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Initialize explorer
        explorer = WebExplorer(exploration_config, ai_config)

        # Perform exploration
        logger.info("Starting website exploration...")
        results = await explorer.explore_website(url)

        # Save exploration results
        results_file = output_path / "exploration_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Exploration results saved to {results_file}")

        # Generate crawling schema
        logger.info("Generating crawling schema...")
        schema_generator = SchemaGenerator()

        domain = url.split('/')[2] if '//' in url else 'unknown'
        schema_name = f"{domain.replace('.', '_')}_schema"

        schema = schema_generator.generate_crawling_schema(results, schema_name)

        # Validate schema
        validation = schema_generator.validate_schema(schema)

        if not validation['is_valid']:
            logger.warning("Schema validation failed:")
            for error in validation['errors']:
                logger.error(f"  - {error}")

        for warning in validation['warnings']:
            logger.warning(f"  - {warning}")

        for recommendation in validation['recommendations']:
            logger.info(f"  - {recommendation}")

        # Save schema
        schema_file = output_path / "crawling_schema.json"
        schema_generator.export_schema(schema, str(schema_file))

        logger.info(f"Crawling schema saved to {schema_file}")

        # Generate Scrapy settings
        scrapy_settings = schema_generator.generate_scrapy_settings(schema)
        settings_file = output_path / "scrapy_settings.py"

        with open(settings_file, 'w') as f:
            f.write("# Scrapy settings generated from exploration\n\n")
            for key, value in scrapy_settings.items():
                f.write(f"{key} = {repr(value)}\n")

        logger.info(f"Scrapy settings saved to {settings_file}")

        # Print summary
        summary = results.get('exploration_summary', {})
        print("\n" + "="*60)
        print("EXPLORATION SUMMARY")
        print("="*60)
        print(f"Website: {url}")
        print(f"Pages visited: {summary.get('total_pages_visited', 0)}")
        print(f"Nodes created: {summary.get('total_nodes_created', 0)}")
        print(f"Series detected: {summary.get('series_detected', 0)}")
        print(f"Max depth reached: {summary.get('max_depth_reached', 0)}")
        print(f"\nOutput directory: {output_path.absolute()}")
        print("="*60)

        return True

    except Exception as e:
        logger.error(f"Exploration failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Website Structure Exploration System for Architecture Materials"
    )

    parser.add_argument(
        'url',
        help='URL to start exploration from'
    )

    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory for results (default: output)'
    )

    parser.add_argument(
        '--config', '-c',
        help='Configuration file path (JSON format)'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Log level (default: INFO)'
    )

    parser.add_argument(
        '--check-env',
        action='store_true',
        help='Check environment configuration and exit'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Check environment if requested
    if args.check_env:
        env_config = get_env_config()
        env_config.print_config_status()

        validation = env_config.validate_required_keys()
        if validation['valid']:
            print("\n[OK] Environment configuration is valid!")
            exit(0)
        else:
            print("\n[ERROR] Environment configuration has errors:")
            for error in validation['errors']:
                print(f"  - {error}")
            exit(1)

    # Run exploration
    success = asyncio.run(explore_website(
        args.url,
        args.output,
        args.config
    ))

    exit(0 if success else 1)


if __name__ == "__main__":
    main()