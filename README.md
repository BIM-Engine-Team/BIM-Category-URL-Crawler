# Website Structure Exploration System

An AI-powered web crawler that explores supplier websites to understand their structure and create crawling schemas for extracting architecture material product information.

## Features

- 🧠 **Claude AI Integration**: Intelligent exploration decisions and pattern detection
- ⚡ **Efficient Crawling**: Link series detection prevents redundant exploration
- 🎯 **Architecture Focus**: Specialized for building materials and supplies
- 📊 **Schema Generation**: Automatic creation of crawling configurations
- 🔄 **Adaptive**: Works across different website structures

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Claude API key from Anthropic

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd crawler

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

**Option 1: Using .env file (Recommended)**
```bash
# Copy the example .env file
cp .env.example .env

# Edit .env file with your API keys
# .env file:
CLAUDE_API_KEY=your_claude_api_key_here
LOG_LEVEL=INFO
OUTPUT_DIR=output
```

**Option 2: Using environment variables**
```bash
# Windows:
set CLAUDE_API_KEY=your_api_key_here
# Linux/Mac:
export CLAUDE_API_KEY=your_api_key_here
```

**Check your configuration:**
```bash
python src/main.py --check-env
```

### 4. Basic Usage

```bash
# Explore a website
python src/main.py https://example-supplier.com

# With custom output directory
python src/main.py https://example-supplier.com --output results

# With configuration file
python src/main.py https://example-supplier.com --config config/sample_config.json

# Debug mode
python src/main.py https://example-supplier.com --log-level DEBUG
```

## Configuration

Copy and customize the sample configuration:

```bash
cp config/sample_config.json config/my_config.json
```

### Key Configuration Options

```json
{
  "exploration": {
    "max_depth": 4,              // Maximum crawling depth
    "max_pages": 200,            // Maximum pages to visit
    "request_delay": 1.5,        // Delay between requests (seconds)
    "architecture_keywords": [    // Target keywords
      "doors", "windows", "roofing"
    ]
  },
  "ai": {
    "model": "claude-3-5-sonnet-20241022",
    "requests_per_minute": 50,   // API rate limiting
    "cache_responses": true      // Cache AI responses
  }
}
```

## Output

The system generates several output files:

- `exploration_results.json` - Raw exploration data
- `crawling_schema.json` - Generated crawling configuration
- `scrapy_settings.py` - Ready-to-use Scrapy settings
- `exploration.log` - Detailed logs

## Example Output Structure

```json
{
  "exploration_summary": {
    "total_pages_visited": 45,
    "series_detected": 3,
    "max_depth_reached": 3
  },
  "website_structure": {
    "nodes": {...},
    "detected_series": {...}
  },
  "crawling_patterns": [...]
}
```

## Advanced Usage

### Custom Architecture Keywords

Modify the configuration to target specific materials:

```json
{
  "exploration": {
    "architecture_keywords": [
      "steel beams", "concrete", "insulation",
      "HVAC", "electrical", "plumbing"
    ]
  }
}
```

### Rate Limiting

Adjust for respectful crawling:

```json
{
  "exploration": {
    "request_delay": 2.0,     // Slower crawling
    "max_pages": 100          // Fewer pages
  }
}
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   ValueError: CLAUDE_API_KEY environment variable is required
   ```
   Solution:
   - Copy `.env.example` to `.env` and add your API key
   - Or set the environment variable: `export CLAUDE_API_KEY=your_key`
   - Check configuration with: `python src/main.py --check-env`

2. **Rate Limiting**
   ```
   WARNING: Request failed (attempt 1): API request failed with status 429
   ```
   Solution: Increase `request_delay` or reduce `requests_per_minute`

3. **Network Errors**
   ```
   ERROR: Timeout for URL: https://example.com
   ```
   Solution: Check internet connection and target website availability

### Debug Mode

Enable debug logging for detailed information:

```bash
python src/main.py https://example.com --log-level DEBUG
```

## API Usage

You can also use the system programmatically:

```python
import asyncio
from src.config.exploration_config import ExplorationConfig
from src.config.ai_config import AIConfig
from src.explorer.web_explorer import WebExplorer

async def explore_site():
    exploration_config = ExplorationConfig()
    ai_config = AIConfig()

    explorer = WebExplorer(exploration_config, ai_config)
    results = await explorer.explore_website("https://example.com")

    return results

# Run exploration
results = asyncio.run(explore_site())
```

## Architecture

The system consists of four main phases:

1. **Data Models**: Core data structures for website representation
2. **AI Integration**: Claude AI for intelligent decision making
3. **Exploration Engine**: Website crawling and analysis
4. **Schema Generation**: Creation of crawling configurations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.