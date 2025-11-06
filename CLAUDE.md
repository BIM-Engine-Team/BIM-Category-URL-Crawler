# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready AI-powered web crawler system designed to intelligently explore supplier websites and extract product information. The system uses AI-guided priority-based exploration with Playwright for dynamic content handling, supporting complex e-commerce sites with JavaScript-heavy interfaces.

## Development Commands

### Installation and Setup
```bash
# Install in development mode (recommended for development)
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser drivers (required)
playwright install

# Environment setup
cp .env.example .env  # Configure API keys
```

### Running the Crawler
```bash
# Console script entry point (after pip install -e .)
ai-crawler config.json

# Direct Python execution
python src/main.py config.json

# Verbose logging (recommended for debugging)
python src/main.py config.json -v
python src/main.py config.json --verbose
```

### TypeScript Integration
```bash
cd typescript-integration
npm install
npm run build

# Example usage
node example/usage.ts
```

### Testing
```bash
# Note: No test suite is currently implemented
# To add tests, consider using pytest for Python:
# pip install pytest
# pytest tests/

# For TypeScript integration:
# cd typescript-integration
# npm test  # (jest configured but no tests written)
```

## Architecture Overview

### AI-Guided Priority Exploration System

The system implements a **priority-based AI-guided exploration** using a max-heap data structure combined with hierarchical tree navigation, fundamentally different from traditional breadth-first or depth-first crawling.

**Core Components:**

1. **AI Crawler Engine** (`src/crawler/ai_crawler.py`):
   - Uses AI scoring (0-10 scale) to prioritize link exploration
   - Implements max-heap (`OpenSet`) with average ancestral scoring
   - Maintains hierarchical website structure (`WebsiteNode`)

2. **AI Scoring Module** (`src/crawler/ai_scoring.py`):
   - Centralized AI interaction for link scoring
   - Product page detection logic
   - Supports multiple AI providers through configuration

3. **Node Processor** (`src/crawler/node_processor.py`):
   - Handles individual node processing and content extraction
   - Coordinates between crawler, dynamic loading, and AI scoring

4. **Dynamic Content Handler** (`src/crawler/dynamic_loading.py`):
   - Playwright-powered detection of dynamic elements
   - Supports: Pagination, Load More, Infinite Scroll, Tabs, Accordions
   - AI-powered pattern identification with targeted waiting strategies

5. **Multi-Provider AI Client** (`src/util/ai_client/`):
   - Abstraction layer for Anthropic Claude, OpenAI, Google
   - JSON configuration-based routing and middleware
   - Standardized prompt system with role-based instructions

6. **Result Cleaner** (`src/util/result_cleaner.py`):
   - Critical post-processing step to remove duplicate products
   - Automatically runs after crawling completes
   - Generates both raw and cleaned output files

### AI Scoring Strategy

- **Scores < 1**: Never explore (marked as explored)
- **Scores > 9**: Product pages (extract info, mark as explored)
- **Scores 1-9**: Add to priority queue for future exploration
- **Average ancestral scoring**: Ensures context-aware prioritization

### Configuration System

**Three-tier configuration:**

1. **Environment Variables** (`.env`): API keys, optional settings
2. **AI Configuration** (`config.json`): Provider and model selection
3. **Task Configuration** (JSON files): Crawl parameters and targets

**Example task configuration:**
```json
{
  "url": "https://example.com",
  "delay": 1.5,
  "max_pages": 100,
  "output": "results.json",
  "enable_dynamic_loading": false
}
```

**Configuration parameters:**
- `url` (required): Starting URL to crawl
- `delay` (optional, default: 1.0): Delay between requests in seconds
- `max_pages` (optional, default: 50): Maximum number of pages to explore
- `output` (optional): Output file path for results
- `enable_dynamic_loading` (optional, default: false): Enable Playwright-based dynamic content detection
- `ai_provider` (optional): Override AI provider (e.g., "anthropic", "openai")
- `ai_model` (optional): Override AI model to use

### System Prompts Architecture

Role-based prompting stored in `src/crawler/system_prompt.json`:
```json
{
  "prompt": "You are an architect. You want to find the product information from a supplier's website."
}
```

Applied consistently across all AI interactions for scoring and dynamic loading detection.

### Key Data Models

- **`WebsiteNode`**: Hierarchical website representation with parent-child relationships
- **`LinkInfo`**: Structured link metadata with AI scoring integration
- **`OpenSet`**: Priority queue implementation with average scoring
- **Dynamic Loading Classes**: Pattern-specific handlers for different dynamic content types

### Dynamic Loading Optimization (Post-2025-09-18)

**Problem Solved**: Eliminated `networkidle` timeouts on analytics-heavy sites
**Solution**: Trigger-specific selector waiting instead of network monitoring
- AI identifies dynamic elements
- Playwright exhausts them with targeted waits
- Avoids infinite waiting on sites with continuous analytics requests

**Important**: Dynamic loading detection is **disabled by default** (as of 2025-11-06) due to performance overhead. Enable it via `enable_dynamic_loading: true` in task configuration when crawling sites with heavy JavaScript/dynamic content (pagination, infinite scroll, load-more buttons, etc.).

### Directory Structure

```
src/
├── crawler/                   # Core crawling logic
│   ├── ai_crawler.py         # Main AI-guided exploration engine
│   ├── ai_scoring.py         # AI scoring module for links
│   ├── node_processor.py     # Node processing coordinator
│   ├── dynamic_loading.py    # Dynamic content detection/handling
│   ├── models.py             # Data models (WebsiteNode, LinkInfo, OpenSet)
│   ├── utils.py              # Utility functions
│   ├── core.py               # Base crawler functionality
│   └── system_prompt.json    # AI prompting configuration
├── util/
│   ├── ai_client/            # Multi-provider AI integration
│   │   ├── ai_middleware.py # Main AI routing layer
│   │   ├── claude_client.py # Anthropic Claude client
│   │   ├── openai_client.py # OpenAI client
│   │   └── google_client.py # Google AI client
│   └── result_cleaner.py     # Duplicate removal post-processor
├── main.py                    # Entry point and CLI interface
└── __init__.py

typescript-integration/        # Node.js/TypeScript wrapper
├── src/index.ts              # Main entry function (mirrors main.py)
├── dist/                     # Compiled JavaScript output
└── example/                  # Usage examples
```

### Package Distribution

- **Python Package**: `bim-category-url-crawler` with console script
- **Console Entry**: `ai-crawler` command after installation
- **TypeScript Wrapper**: Single-entry function design in `typescript-integration/`
  - Function: `aiCrawler(configPath)` - mirrors Python `main.py` behavior
  - Spawns Python process, handles output parsing, returns structured results
- **Development Installation**: `pip install -e .` for local development

### Output Pipeline

The crawler generates two output files:
1. **Raw results** (`*_raw.json`): Unprocessed crawl results with potential duplicates
2. **Final results** (`*.json`): Cleaned results after duplicate removal

The duplicate cleaning step (`main.py:103-111`) is **critical** and automatically runs after crawling completes. This step:
- Removes duplicate product entries
- Normalizes product data
- Ensures result quality

### Documentation Workflow

Structured feature development using templates in `docs/features/commands/`:
- `@plan_feature.md`: Technical planning
- `@create_brief.md`: Product briefs
- `@code_review.md`: Implementation review
- `@write_docs.md`: Documentation creation

Plans saved as `docs/features/NNNN_*.md` with incremental numbering.

## Important Notes for Development

### Modifying AI Behavior
- System prompts are centralized in `src/crawler/system_prompt.json`
- AI provider/model can be overridden via task config or environment variables
- All AI interactions flow through `src/util/ai_client/ai_middleware.py`

### Working with Dynamic Loading
- New dynamic loading patterns should be added to `dynamic_loading.py`
- Each pattern has a dedicated handler class (e.g., `PaginationHandler`, `LoadMoreHandler`)
- Always use selector-based waiting, not network idle timeouts

### Configuration Hierarchy
1. **Environment variables** (`.env`) - API keys, optional overrides
2. **Task config** (JSON file) - Per-crawl settings
3. **Code defaults** - Fallback values in source code

Config precedence: Task config > Environment variables > Code defaults

### Adding New AI Providers
1. Create new client in `src/util/ai_client/` (follow existing client patterns)
2. Register in `ai_middleware.py`
3. Update configuration examples

### Common Pitfalls
- **Missing Playwright**: Always run `playwright install` after pip install
- **API Keys**: Ensure `.env` file is configured (copy from `.env.example`)
- **Result Files**: Always check both raw and cleaned output files
- **Module Imports**: Use absolute imports from `src` package root