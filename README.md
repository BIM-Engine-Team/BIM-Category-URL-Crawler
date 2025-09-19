# AI-Powered Web Crawler with Dynamic Loading Support

An intelligent web crawler system that uses AI to automatically explore supplier websites and extract architecture material product information. The system features AI-guided navigation, dynamic content handling, and smart link prioritization.

## Features

### Core Capabilities
- **AI-Guided Navigation**: Uses AI to intelligently score and prioritize links for exploration
- **Dynamic Loading Detection**: Automatically detects and handles various types of dynamic content:
  - Pagination
  - Load More buttons
  - Infinite Scroll
  - Tabs
  - Accordions
  - Expanders
- **Smart Link Series Detection**: Avoids redundant exploration of similar link patterns
- **Priority-Based Exploration**: Uses scoring system to focus on most relevant content
- **Product Information Extraction**: Automatically identifies and extracts product pages

### Technical Features
- **Robust Error Handling**: Comprehensive timeout and error management for dynamic content
- **Playwright Integration**: Uses Playwright for reliable browser automation
- **Domain-Aware Crawling**: Stays within specified domains and handles relative/absolute URLs
- **Rate Limiting**: Configurable delays to respect website resources
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## How It Works

### Main Workflow
1. **Start Crawling**: Begin from the configured base URL
2. **Extract Links**: Discover all links on the current page
3. **AI Scoring**: AI evaluates each link's relevance (0-10 scale)
4. **Dynamic Loading Check**: Detect if page uses dynamic content loading
5. **Content Exhaustion**: Use Playwright to interact with dynamic elements
6. **Priority Queue**: Add discovered links to exploration queue based on scores
7. **Product Detection**: Identify and extract product pages (score > 9)
8. **Continue Exploration**: Process next highest-scored page

### Dynamic Loading Detection Process
1. **AI Analysis**: AI examines page structure and UI elements
2. **Element Identification**: Maps detected elements to interaction types
3. **Playwright Automation**: Executes clicks, scrolls, tab switches, etc.
4. **Content Extraction**: Discovers additional links from revealed content
5. **Validation**: Ensures new links are valid and within domain scope
6. **Queue Integration**: Adds new links to main exploration priority queue

## Installation & Setup

### Prerequisites
- Python 3.13.5+
- Virtual environment recommended

### Environment Setup

1. **Clone and setup the repository:**
```bash
git clone <repository-url>
cd crawler
```

2. **Create and activate virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Configure environment variables:**
```bash
# Copy example configuration
cp .env.example .env

# Edit .env file with your settings:
# CLAUDE_API_KEY=your_api_key_here
# OUTPUT_DIR=output
# LOG_LEVEL=INFO
```

## Usage

### Basic Usage

Run the crawler with a configuration file:

```bash
python src/main.py example_config.json --verbose
```

### Configuration File Format

Create a JSON configuration file with the following structure:

```json
{
  "url": "https://www.example-supplier.com",
  "delay": 1.5,
  "max_pages": 100,
  "output": "supplier_products.json"
}
```

**Configuration Parameters:**
- `url`: Target website URL to crawl
- `delay`: Delay between requests in seconds (default: 1.0)
- `max_pages`: Maximum number of pages to crawl (default: 50)
- `output`: Output file path for results (optional, auto-generated if not specified)

### Example Usage

```bash
# Basic crawling with default settings
python src/main.py my_config.json

# Verbose output for debugging
python src/main.py my_config.json --verbose

# Example configuration for a paint supplier
echo '{
  "url": "https://www.sherwin-williams.com",
  "delay": 2.0,
  "max_pages": 150,
  "output": "paint_products.json"
}' > paint_config.json

python src/main.py paint_config.json
```

## System Components

### Core Modules

#### `src/crawler/ai_crawler.py`
- **AIGuidedCrawler**: Main crawler class with AI integration
- Handles priority-based exploration using AI scoring
- Integrates with dynamic loading detection at `ai_crawler.py:182`
- Manages product discovery and extraction

#### `src/crawler/dynamic_loading.py`
- **DynamicLoadingHandler**: Handles all types of dynamic content
- AI-powered detection of dynamic loading patterns using `_check_with_ai()` at `dynamic_loading.py:99`
- Playwright-based interaction automation
- Content exhaustion strategies for each interaction type

#### `src/crawler/models.py`
- **LinkInfo**: Data structure for link information with ID mapping for AI scoring
- **WebsiteNode**: Tree structure for website hierarchy
- **OpenSet**: Priority queue for exploration ordering

#### `src/util/ai_client/`
- AI client middleware for various AI services
- Supports Claude, OpenAI, and Google AI platforms
- Unified interface for AI prompting and response parsing

### Key Features Implementation

#### AI-Guided Scoring
The system uses AI to score each discovered link on a 0-10 scale:
- **0-1**: Irrelevant links (skipped)
- **1-9**: Potentially useful links (queued for exploration)
- **9-10**: Product pages (extracted immediately)

#### Dynamic Loading Detection
The main integration happens in `ai_crawler.py:182` where after processing regular links with scores > 1.0, the system calls `check_and_exhaust_dynamic_loading()` to:

1. **AI Analysis**: Examines page structure to identify dynamic elements
2. **Element Identification**: Maps UI elements to interaction types (Pagination, Load More, Tabs, etc.)
3. **Playwright Automation**: Executes interactions to reveal content
4. **Content Extraction**: Discovers and validates new links
5. **Queue Integration**: Adds new links to exploration priority queue with proper scoring

#### Robust Wait Strategies
The system implements multiple waiting strategies in `dynamic_loading.py` for reliable dynamic content handling:
- **Content-Specific Selectors**: Waits for pagination content at `dynamic_loading.py:316-347`
- **Loading Indicator Monitoring**: Tracks loading states at `dynamic_loading.py:397-434`
- **State Change Detection**: Monitors DOM changes and element visibility
- **Fallback Timeouts**: Graceful handling when content doesn't load as expected

## Output Format

The crawler generates JSON output with discovered products:

```json
{
  "products": [
    {
      "productName": "Premium Interior Paint",
      "url": "https://www.example.com/products/premium-interior-paint"
    }
  ],
  "summary": {
    "pages_processed": 45,
    "total_nodes": 128,
    "products_found": 23,
    "crawl_time": "2025-09-19T10:30:00Z"
  }
}
```

## Dynamic Loading Types Supported

### Pagination
- Detects and clicks through pagination controls
- Waits for new content using multiple selector strategies
- Prevents infinite loops with max page limits

### Load More Buttons
- Identifies and repeatedly clicks "Load More" buttons
- Monitors content changes to detect when no new content loads
- Handles dynamic button repositioning

### Infinite Scroll
- Always checked regardless of AI detection results
- Scrolls to bottom and waits for new content
- Detects height changes to determine when to stop

### Tabs
- Clicks tab elements to reveal hidden content
- Waits for tab content to become visible using `aria-hidden` attributes
- Extracts links from activated tab panels

### Accordions & Expanders
- Clicks accordion headers and expander controls
- Waits for content expansion using `aria-expanded` attributes
- Monitors height changes to confirm content is revealed

## Troubleshooting

### Common Issues

**Dynamic content not loading:**
- Increase delay in configuration
- Check network connectivity
- Verify AI API key configuration

**AI scoring failures:**
- Ensure API key is valid and has sufficient credits
- Check internet connectivity for AI service calls
- Review logs for specific error messages

**Browser automation issues:**
- Ensure Playwright chromium is installed: `playwright install chromium`
- Check for system dependencies on Linux
- Verify sufficient system resources (RAM/CPU)

### Logging and Debugging

Enable verbose logging for detailed information:
```bash
python src/main.py config.json --verbose
```

Log levels and their purposes:
- **INFO**: General progress and results
- **DEBUG**: Detailed operation information
- **ERROR**: Error conditions and failures
- **WARNING**: Non-critical issues and fallbacks

Key log messages to monitor:
- `[DYNAMIC_LOADING]` prefix for dynamic content processing
- `[PAGE_PROCESSING]` prefix for main crawler operations
- JSON parsing errors in AI response handling

### Performance Optimization

**For large websites:**
- Reduce `max_pages` parameter
- Increase `delay` to be more respectful
- Monitor system resources during crawling

**For dynamic-heavy sites:**
- Adjust timeout values in `dynamic_loading.py`
- Consider site-specific wait strategies
- Test with smaller page limits first

## Development

### Project Structure
```
crawler/
├── src/
│   ├── crawler/           # Core crawler modules
│   │   ├── ai_crawler.py     # Main AI-guided crawler
│   │   ├── dynamic_loading.py # Dynamic content handler
│   │   ├── models.py         # Data structures
│   │   └── utils.py          # Utility functions
│   ├── util/
│   │   └── ai_client/        # AI integration modules
│   └── main.py              # Entry point
├── docs/features/          # Technical documentation
├── example_config.json     # Example configuration
└── README.md              # This file
```

### Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive logging for new features
3. Update documentation for any new functionality
4. Test with various website types and configurations
5. Ensure backward compatibility with existing configurations

## License

This project is designed for educational and research purposes. Ensure compliance with website terms of service and robots.txt when crawling.