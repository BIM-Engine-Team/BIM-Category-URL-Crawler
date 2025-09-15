#!/usr/bin/env python3
"""
Basic usage example for the Website Structure Exploration System
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.config.exploration_config import ExplorationConfig
from src.config.ai_config import AIConfig
from src.explorer.web_explorer import WebExplorer
from src.schema.schema_generator import SchemaGenerator


async def basic_exploration_example():
    """
    Basic example of exploring a website
    """
    print("🔍 Basic Website Exploration Example")
    print("=" * 50)

    # Check API key using environment configuration
    from src.config.env_config import get_env_config

    env_config = get_env_config()
    validation = env_config.validate_required_keys()

    if not validation['valid']:
        print("❌ Environment configuration errors:")
        for error in validation['errors']:
            print(f"  - {error}")
        print("\nSolutions:")
        print("1. Copy .env.example to .env and add your CLAUDE_API_KEY")
        print("2. Or set environment variable: export CLAUDE_API_KEY=your_key")
        print("3. Check with: python src/main.py --check-env")
        return False

    # Show any warnings
    for warning in validation['warnings']:
        print(f"⚠️  {warning}")

    # Configure exploration settings
    exploration_config = ExplorationConfig(
        max_depth=3,           # Limit depth for testing
        max_pages=20,          # Limit pages for testing
        request_delay=2.0      # Be respectful
    )

    ai_config = AIConfig()

    print(f"📋 Configuration:")
    print(f"   Max depth: {exploration_config.max_depth}")
    print(f"   Max pages: {exploration_config.max_pages}")
    print(f"   Request delay: {exploration_config.request_delay}s")
    print()

    # Example URL - replace with actual target
    target_url = "https://httpbin.org"  # Safe testing URL
    print(f"🎯 Target URL: {target_url}")

    try:
        # Create explorer
        explorer = WebExplorer(exploration_config, ai_config)

        # Perform exploration
        print("🚀 Starting exploration...")
        results = await explorer.explore_website(target_url)

        # Display results
        summary = results.get('exploration_summary', {})
        print("\n📊 Exploration Results:")
        print(f"   Pages visited: {summary.get('total_pages_visited', 0)}")
        print(f"   Nodes created: {summary.get('total_nodes_created', 0)}")
        print(f"   Series detected: {summary.get('series_detected', 0)}")
        print(f"   Max depth: {summary.get('max_depth_reached', 0)}")

        # Save results
        output_dir = Path("example_output")
        output_dir.mkdir(exist_ok=True)

        results_file = output_dir / "basic_exploration_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {results_file}")

        # Generate schema
        print("\n🔧 Generating crawling schema...")
        schema_generator = SchemaGenerator()
        schema = schema_generator.generate_crawling_schema(results, "example_schema")

        schema_file = output_dir / "crawling_schema.json"
        schema_generator.export_schema(schema, str(schema_file))

        print(f"📄 Schema saved to: {schema_file}")

        print("\n✅ Basic exploration completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Exploration failed: {e}")
        return False


async def test_components_example():
    """
    Example testing individual components
    """
    print("\n🧪 Component Testing Example")
    print("=" * 50)

    # Test HTTP client
    print("Testing HTTP Client...")
    from src.utils.http_client import HTTPClient

    async with HTTPClient(request_delay=1.0) as client:
        response = await client.get("https://httpbin.org/html")
        if response:
            print(f"✅ HTTP Client works - Status: {response['status']}")
        else:
            print("❌ HTTP Client failed")

    # Test page analyzer
    print("\nTesting Page Analyzer...")
    from src.explorer.page_analyzer import PageAnalyzer

    analyzer = PageAnalyzer()
    if response and response['content']:
        links = analyzer.extract_links(response['content'], "https://httpbin.org")
        metadata = analyzer.extract_page_metadata(response['content'], "https://httpbin.org")

        print(f"✅ Page Analyzer works - Found {len(links)} links")
        print(f"   Page title: {metadata.get('title', 'N/A')}")

    # Test configuration
    print("\nTesting Configuration...")
    exploration_config = ExplorationConfig()
    print(f"✅ ExplorationConfig loaded - Keywords: {len(exploration_config.architecture_keywords)}")

    ai_config = AIConfig()
    print(f"✅ AIConfig loaded - Model: {ai_config.model}")

    print("\n✅ All components tested successfully!")


async def mock_exploration_example():
    """
    Example with mock data (no AI calls)
    """
    print("\n🎭 Mock Exploration Example (No AI)")
    print("=" * 50)

    # Create mock exploration results
    mock_results = {
        'exploration_summary': {
            'start_url': 'https://example-supplier.com',
            'total_pages_visited': 15,
            'total_nodes_created': 12,
            'series_detected': 2,
            'max_depth_reached': 3
        },
        'website_structure': {
            'nodes': {
                'https://example-supplier.com': {
                    'url': 'https://example-supplier.com',
                    'node_type': 'homepage',
                    'children': ['https://example-supplier.com/products'],
                    'exploration_status': 'explored',
                    'is_terminal': False,
                    'link_series': None
                },
                'https://example-supplier.com/products': {
                    'url': 'https://example-supplier.com/products',
                    'node_type': 'category',
                    'children': [],
                    'exploration_status': 'explored',
                    'is_terminal': False,
                    'link_series': {
                        'pattern_id': 'products_pagination',
                        'url_pattern': '/products?page={num}',
                        'sample_urls': [
                            'https://example-supplier.com/products?page=1',
                            'https://example-supplier.com/products?page=2'
                        ],
                        'total_count': 10,
                        'series_type': 'pagination'
                    }
                }
            },
            'detected_series': {},
            'visited_urls': [
                'https://example-supplier.com',
                'https://example-supplier.com/products'
            ]
        },
        'crawling_patterns': [
            {
                'type': 'series',
                'pattern': '/products?page={num}',
                'series_type': 'pagination',
                'estimated_count': 10
            }
        ]
    }

    # Generate schema from mock data
    print("📊 Mock exploration results:")
    summary = mock_results['exploration_summary']
    for key, value in summary.items():
        print(f"   {key}: {value}")

    # Generate schema
    print("\n🔧 Generating schema from mock data...")
    schema_generator = SchemaGenerator()
    schema = schema_generator.generate_crawling_schema(mock_results, "mock_schema")

    # Validate schema
    validation = schema_generator.validate_schema(schema)
    print(f"\n✅ Schema validation: {'Passed' if validation['is_valid'] else 'Failed'}")

    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"   ⚠️  {warning}")

    if validation['recommendations']:
        for rec in validation['recommendations']:
            print(f"   💡 {rec}")

    # Save mock results
    output_dir = Path("example_output")
    output_dir.mkdir(exist_ok=True)

    mock_file = output_dir / "mock_results.json"
    with open(mock_file, 'w', encoding='utf-8') as f:
        json.dump(mock_results, f, indent=2, ensure_ascii=False)

    schema_file = output_dir / "mock_schema.json"
    schema_generator.export_schema(schema, str(schema_file))

    print(f"\n💾 Mock results saved to: {mock_file}")
    print(f"📄 Mock schema saved to: {schema_file}")

    print("\n✅ Mock exploration example completed!")


async def main():
    """
    Run all examples
    """
    print("🚀 Website Exploration System Examples")
    print("=" * 60)

    # Run component tests (no API key needed)
    await test_components_example()

    # Run mock example (no API key needed)
    await mock_exploration_example()

    # Run basic exploration (requires API key)
    if os.getenv('CLAUDE_API_KEY'):
        await basic_exploration_example()
    else:
        print("\n⚠️  Skipping AI-powered examples (CLAUDE_API_KEY not set)")
        print("Set your API key to test full functionality:")
        print("export CLAUDE_API_KEY=your_key_here")

    print("\n🎉 All examples completed!")
    print("\nNext steps:")
    print("1. Review the generated files in example_output/")
    print("2. Try with a real supplier website")
    print("3. Customize configuration in config/sample_config.json")


if __name__ == "__main__":
    asyncio.run(main())