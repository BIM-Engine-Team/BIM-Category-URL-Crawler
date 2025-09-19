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

# Verbose logging
python src/main.py config.json -v
```

### TypeScript Integration
```bash
cd typescript-integration
npm install && npm run build
```

## Architecture Overview

### AI-Guided Priority Exploration System

The system implements a **priority-based AI-guided exploration** using a max-heap data structure combined with hierarchical tree navigation, fundamentally different from traditional breadth-first or depth-first crawling.

**Core Components:**

1. **AI Crawler Engine** (`src/crawler/ai_crawler.py`):
   - Uses AI scoring (0-10 scale) to prioritize link exploration
   - Implements max-heap (`OpenSet`) with average ancestral scoring
   - Maintains hierarchical website structure (`WebsiteNode`)

2. **Dynamic Content Handler** (`src/crawler/dynamic_loading.py`):
   - Playwright-powered detection of dynamic elements
   - Supports: Pagination, Load More, Infinite Scroll, Tabs, Accordions
   - AI-powered pattern identification with targeted waiting strategies

3. **Multi-Provider AI Client** (`src/util/ai_client/`):
   - Abstraction layer for Anthropic Claude, OpenAI, Google
   - JSON configuration-based routing and middleware
   - Standardized prompt system with role-based instructions

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
  "output": "results.json"
}
```

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

### Directory Structure

```
src/
├── crawler/           # Core crawling logic
│   ├── ai_crawler.py         # Main AI-guided exploration engine
│   ├── dynamic_loading.py    # Dynamic content detection/handling
│   └── system_prompt.json    # AI prompting configuration
├── util/
│   ├── ai_client/     # Multi-provider AI integration
│   ├── link_utils.py  # URL processing and validation
│   └── website_node.py # Tree data structure
└── main.py            # Entry point and CLI interface
```

### Package Distribution

- **Python Package**: `bim-category-url-crawler` with console script
- **Console Entry**: `ai-crawler` command after installation
- **TypeScript Wrapper**: Node.js integration in `typescript-integration/`
- **Development Installation**: `pip install -e .` for local development

### Documentation Workflow

Structured feature development using templates in `docs/features/commands/`:
- `@plan_feature.md`: Technical planning
- `@create_brief.md`: Product briefs
- `@code_review.md`: Implementation review
- `@write_docs.md`: Documentation creation

Plans saved as `docs/features/NNNN_*.md` with incremental numbering.