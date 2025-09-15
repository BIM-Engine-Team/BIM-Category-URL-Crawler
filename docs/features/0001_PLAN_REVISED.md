# Website Structure Exploration System - Revised Plan

## Overview

Build an AI-powered web crawler that explores supplier websites to understand their structure and create crawling schemas for extracting architecture material product information. Uses Claude AI for intelligent exploration decisions and pattern detection to optimize crawling efficiency.

## Core Components

### Phase 1: Essential Data Models

#### Key Files:

- `src/models/website_node.py` - Website structure node
- `src/models/link_series.py` - Similar link pattern grouping
- `src/models/exploration_state.py` - Exploration state tracking
- `src/config/exploration_config.py` - Configuration
- `src/utils/http_client.py` - HTTP client
- `src/ai/exploration_ai.py` - Claude AI integration for exploration decisions and termination

#### Core Data Structures:

```python
class LinkSeries:
    pattern_id: str
    url_pattern: str  # e.g., "/products?page={num}"
    sample_urls: List[str]  # 3-5 representative samples
    total_count: int
    series_type: str  # 'pagination', 'category', 'product_variant'

class WebsiteNode:
    url: str
    node_type: str  # 'homepage', 'category', 'product', 'listing'
    children: List[str]
    link_series: Optional[LinkSeries]
    exploration_status: str  # 'explored', 'skipped', 'series_sample', 'leaf'
    is_terminal: bool  # Claude-determined leaf node status

class ExplorationState:
    visited_urls: Set[str]
    tree_nodes: Dict[str, WebsiteNode]
    detected_series: Dict[str, LinkSeries]
    exploration_queue: List[str]
    current_depth: int
```

### Phase 2: AI Integration Layer

#### Key Files:

- `src/ai/base_ai_client.py` - Base Claude AI client with authentication and error handling
- `src/ai/exploration_ai.py` - Claude AI integration for exploration decisions and termination
- `src/ai/series_detection_ai.py` - Claude AI integration for link series detection
- `src/ai/link_relevance_ai.py` - Claude AI integration for link relevance filtering
- `src/ai/content_classifier_ai.py` - Claude AI for classifying page types and content relevance
- `src/ai/prompt_templates.py` - Structured prompts for different AI tasks
- `src/config/ai_config.py` - AI configuration and API keys

#### Core AI Components:

```python
class BaseAIClient:
    api_key: str
    model: str  # claude-sonnet-4-20250514
    rate_limiter: RateLimiter
    error_handler: AIErrorHandler

class ExplorationAI:
    # Determines which links to explore next based on context
    # Decides when to stop exploring (leaf node detection)
    # Provides exploration strategy recommendations

class SeriesDetectionAI:
    # Identifies link patterns and groups similar URLs
    # Selects representative samples from detected series
    # Classifies series types (pagination, categories, variants)

class LinkRelevanceAI:
    # Filters links based on architecture material relevance
    # Scores link importance for exploration priority
    # Identifies non-relevant sections to skip

class ContentClassifierAI:
    # Classifies page types (homepage, category, product, listing)
    # Determines content relevance for architecture materials
    # Extracts key metadata for schema generation
```

#### AI Integration Features:

- **Intelligent Decision Making**: Claude AI guides exploration strategy based on website structure patterns
- **Content Understanding**: AI classifies and filters content for architecture material relevance
- **Pattern Recognition**: Advanced link series detection using natural language understanding
- **Adaptive Exploration**: AI adjusts exploration depth and breadth based on site complexity
- **Error Recovery**: AI-powered fallback strategies for failed requests or parsing errors

#### Rate Limiting & Error Handling:

- Request throttling to respect Claude API limits
- Exponential backoff for API failures
- Graceful degradation when AI services are unavailable
- Caching of AI responses for similar patterns

### Phase 3: Exploration Engine

#### Key Files:

- `src/explorer/web_explorer.py` - Main exploration orchestrator
- `src/explorer/page_analyzer.py` - Page structure analysis
- `src/ai/series_detection_ai.py` - Claude AI integration for link series detection
- `src/ai/link_relevance_ai.py` - Claude AI integration for link relevance filtering

#### Core Algorithm:

1. **Start from homepage** - Extract navigation and key links
2. **Claude-guided link selection** - Claude AI decides which links to explore next based on context
3. **Claude exploration control** - Claude AI determines when to stop exploring and identifies leaf nodes
4. **Claude series detection** - Claude AI identifies link patterns and groups similar URLs
5. **Claude relevance filtering** - Claude AI filters out irrelevant links during tree building
6. **Sample exploration** - Explore selected samples from each detected series
7. **Build structure tree** - Create hierarchical website map

#### Claude-Powered Link Series Detection:

- Claude AI analyzes link patterns and identifies series like `/category/{name}`, `/products?page={num}`
- Groups similar links to avoid redundant exploration
- Claude AI selects diverse, representative samples from each series
- Filters out individual links already covered by detected series

### Phase 4: Schema Generation

#### Key Files:

- `src/schema/schema_generator.py` - Generate crawling patterns
- `src/schema/pattern_extractor.py` - Extract common data fields

#### Output:

- Website structure tree (JSON)
- URL patterns for crawling
- Data extraction rules for product information

## Configuration

### Exploration Limits:

- Max depth: 4 levels
- Max pages: 200 per domain
- Link series: Min 3 similar links, max 5 samples per series
- Request delay: 1-2 seconds between requests

### Content Focus:

- Architecture material keywords: doors, windows, roofing, flooring, etc.
- Skip: legal pages, contact forms, user accounts
- Prioritize: product catalogs, category pages, specifications

## Key Benefits of This Approach

1. **Efficiency**: Link series detection prevents exploring hundreds of similar pages
2. **Intelligence**: Focus on architecture-relevant content only
3. **Scalability**: Sample-based exploration works for large websites
4. **Adaptability**: Pattern detection works across different site structures

## Implementation Priority

**Phase 1**: Data models and HTTP client (foundational)
**Phase 2**: AI integration layer (core intelligence components)
**Phase 3A**: Basic exploration without series detection (validate approach)
**Phase 3B**: Add link series detection (optimize efficiency)
**Phase 4**: Schema generation (enable crawling)
