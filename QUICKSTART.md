# Quick Start Guide

Get up and running with the Website Structure Exploration System in 5 minutes.

## 1. Prerequisites

- Python 3.8 or higher
- Claude API key from Anthropic ([Get one here](https://console.anthropic.com/))

## 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd crawler

# Run automated setup
python setup.py
```

The setup script will:
- ✓ Check Python version
- ✓ Install dependencies
- ✓ Create .env file from template
- ✓ Test installation

## 3. Configure API Key

**Method 1: Edit .env file (Recommended)**
```bash
# The setup script created a .env file for you
# Edit it and add your API key:

# .env file:
CLAUDE_API_KEY=your_actual_api_key_here
LOG_LEVEL=INFO
OUTPUT_DIR=output
```

**Method 2: Environment variable**
```bash
# Windows:
set CLAUDE_API_KEY=your_api_key_here

# Linux/Mac:
export CLAUDE_API_KEY=your_api_key_here
```

## 4. Verify Setup

```bash
# Check configuration
python src/main.py --check-env

# Should output:
# Environment Configuration Status:
# ✓ .env file loaded: /path/to/.env
# ✓ CLAUDE_API_KEY: Set (length: 108)
# ✓ LOG_LEVEL: INFO
# ✓ OUTPUT_DIR: output
```

## 5. First Exploration

```bash
# Test with a simple website
python src/main.py https://httpbin.org --output test_results

# For architecture materials suppliers:
python src/main.py https://supplier-website.com --output supplier_results
```

## 6. Check Results

```bash
# View generated files
ls test_results/

# Files created:
# - exploration_results.json    # Raw exploration data
# - crawling_schema.json        # Generated crawling schema
# - scrapy_settings.py         # Ready-to-use Scrapy settings
# - exploration.log            # Detailed logs
```

## 7. Customize Configuration (Optional)

```bash
# Copy sample configuration
cp config/sample_config.json config/my_config.json

# Edit configuration
# Then use it:
python src/main.py https://website.com --config config/my_config.json
```

## Common Commands

```bash
# Help
python src/main.py --help

# Check environment
python src/main.py --check-env

# Debug mode
python src/main.py https://website.com --log-level DEBUG

# Custom output directory
python src/main.py https://website.com --output my_results

# With custom config
python src/main.py https://website.com --config my_config.json
```

## Example Output

```json
{
  "exploration_summary": {
    "total_pages_visited": 25,
    "total_nodes_created": 20,
    "series_detected": 3,
    "max_depth_reached": 3
  },
  "crawling_patterns": [
    {
      "type": "series",
      "pattern": "/products?page={num}",
      "series_type": "pagination",
      "estimated_count": 15
    }
  ]
}
```

## Troubleshooting

**Problem: API key not found**
```
Environment configuration errors:
- CLAUDE_API_KEY is required
```
**Solution:** Edit `.env` file and add your API key

**Problem: Import errors**
```
ModuleNotFoundError: No module named 'aiohttp'
```
**Solution:** Run `python setup.py` or `pip install -r requirements.txt`

**Problem: Rate limiting**
```
API request failed with status 429
```
**Solution:** Increase `request_delay` in configuration

## Next Steps

1. **Explore real websites** - Try architecture material suppliers
2. **Customize keywords** - Edit `architecture_keywords` in config
3. **Generate scrapers** - Use the generated schema with Scrapy
4. **Scale up** - Increase `max_pages` and `max_depth` for larger sites

## Support

- Check logs in `exploration.log`
- Run with `--log-level DEBUG` for detailed information
- Review configuration with `--check-env`

Happy crawling! 🕷️