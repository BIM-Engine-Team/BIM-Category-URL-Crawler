# AI-Powered Web Crawler

An intelligent web crawler system that uses AI to automatically explore supplier websites and discover product pages. The system employs AI-guided navigation to efficiently find architecture material product information.

## Features

- **AI-Guided Exploration**: Uses AI to score and prioritize links based on likelihood of leading to product pages
- **Priority-Based Navigation**: Implements a max binary heap to explore the most promising paths first
- **Product Discovery**: Automatically identifies product pages and extracts product names
- **Domain-Focused Crawling**: Stays within the target domain to maintain relevance
- **Configurable Parameters**: Supports JSON configuration files for flexible execution
- **Structured Results**: Outputs detailed JSON results with discovered products

## Architecture

The system implements a three-phase architecture:

1. **EXPLORE PHASE** (Current Implementation): AI agent explores websites to build structural tree
2. **SCHEMA PHASE** (Future): Generate crawling schemas from exploration data
3. **EXECUTE PHASE** (Future): Use schemas to extract product data

### Key Components

- **WebsiteNode**: Tree structure representing website hierarchy with AI scoring
- **OpenSet**: Max binary heap priority queue for exploration ordering
- **AIGuidedCrawler**: Main crawler class with AI integration
- **LinkInfo**: Structured link information extraction

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crawler
```

2. Set up Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your CLAUDE_API_KEY
```

## Usage

### Basic Usage

Run the AI-guided crawler with a task configuration file:

```bash
python src/main.py example_task_config.json
```

### Task Configuration

Create a JSON configuration file with the following structure:

```json
{
    "url": "https://www.sherwin-williams.com",
    "delay": 1.5,
    "max_pages": 30,
    "output": "sherwin_williams_products.json"
}
```

**Configuration Parameters:**
- `url`: Starting URL for crawling (required)
- `delay`: Delay between requests in seconds (default: 1.0)
- `max_pages`: Maximum number of pages to explore (default: 50)
- `output`: Output file for results (optional, auto-generated if not specified)

### Example Configuration Files

See `example_task_config.json` for a complete example configuration.

## AI Scoring System

The AI evaluates each link on a 0-10 scale:

- **0-1**: Links that will never be clicked (navigation, legal pages, etc.)
- **1-9**: Links with varying likelihood of leading to products (explored further)
- **9-10**: Very likely product pages (marked as products and exploration stops)

When a link scores 9+, the AI also provides the product name for extraction.

## Output

The crawler generates detailed JSON results:

```json
{
  "products": [
    {
      "productName": "Emerald Urethane Trim Enamel",
      "url": "https://example.com/products/emerald-urethane"
    }
  ],
  "pages_processed": 25,
  "total_nodes": 147,
  "base_url": "https://example.com",
  "domain": "example.com"
}
```

## Testing

Run the test suite to verify installation:

```bash
python test_ai_crawler.py
```

The test validates:
- Core data structure functionality
- OpenSet priority queue operations
- Task configuration loading
- Basic crawler initialization

## Project Structure

```
crawler/
├── src/
│   ├── crawler/
│   │   ├── __init__.py          # Package exports
│   │   ├── core.py              # Original BFS crawler
│   │   ├── ai_crawler.py        # AI-guided crawler
│   │   ├── models.py            # Data structures
│   │   └── utils.py             # Utility functions
│   ├── util/
│   │   └── ai_client/           # AI middleware
│   └── main.py                  # Main entry point
├── docs/features/               # Technical documentation
├── example_task_config.json     # Example configuration
├── test_ai_crawler.py          # Test suite
└── README.md                   # This file
```

## Development

### Adding New Features

1. Review technical plans in `docs/features/`
2. Follow existing code patterns and conventions
3. Add tests for new functionality
4. Update documentation

### AI Integration

The system uses the existing `ai_middleware.py` interface for AI communication. Ensure your environment has the necessary AI API keys configured.

## Logging

The crawler provides detailed logging:
- Progress updates during exploration
- Product discovery notifications
- Error handling for failed requests
- AI scoring results

Use `--verbose` flag for debug-level logging:

```bash
python src/main.py config.json --verbose
```

## Limitations

- Currently implements only the EXPLORE phase
- Requires AI API access for scoring functionality
- Limited to single-domain crawling
- No built-in rate limiting beyond basic delays

## Future Enhancements

- Schema generation phase implementation
- Multi-domain crawling support
- Advanced rate limiting and politeness policies
- Caching and resume functionality
- Web UI for configuration and monitoring

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]