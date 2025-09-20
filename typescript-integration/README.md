# AI Product Category Crawler - TypeScript Integration

TypeScript/Node.js wrapper for the AI-guided product category crawler Python package.

This crawler intelligently discovers product pages on supplier websites using AI to guide exploration and handle dynamic content like pagination, load-more buttons, tabs, and infinite scroll.

## 🚀 Quick Start for TypeScript Projects

### Prerequisites

- Node.js ≥ 16.0.0
- Python ≥ 3.8 with pip
- Claude API key from [Anthropic](https://console.anthropic.com/)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/bim-category-url-crawler.git
cd bim-category-url-crawler
```

### Step 2: Install Python Package

```bash
# Install the Python crawler package locally
pip install -e .
```

### Step 3: Build TypeScript Wrapper

```bash
cd typescript-integration
npm install
npm run build
```

### Step 4: Environment Setup

Create a `.env` file in your TypeScript project root:

```env
CLAUDE_API_KEY=your_claude_api_key_here
```

## 💻 Usage in Your TypeScript Project

### Simple Entry Function (Recommended)

The package now provides a single entry function that mirrors the Python `main.py` behavior:

```typescript
// src/crawler-service.ts
import aiCrawler from './path/to/typescript-integration/dist/index';
// or if installed via npm: import aiCrawler from 'bim-category-url-crawler';

export class ProductCrawlerService {
  async crawlProducts(configPath: string) {
    try {
      // Single function call - just like Python main.py
      const results = await aiCrawler(configPath);

      console.log(`Found ${results.products.length} products!`);
      console.log(`Processed ${results.pages_processed} pages`);
      console.log(`Total nodes discovered: ${results.total_nodes}`);

      return {
        success: true,
        data: results
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}
```

### Config File Format

Create your config file in JSON format (same as Python main.py expects):

```json
{
  "url": "https://www.sherwin-williams.com",
  "delay": 1.5,
  "max_pages": 50,
  "output": "crawl_results.json",
  "ai_provider": "anthropic",
  "ai_model": "claude-sonnet-4-20250514"
}
```

### Complete Example Application

```typescript
// src/main.ts
import aiCrawler from './path/to/typescript-integration/dist/index';
import * as path from 'path';

async function main() {
  try {
    // Path to your config file (same format as Python main.py expects)
    const configPath = path.join(__dirname, 'config.json');

    // Call the crawler with config file path - mirrors Python main.py behavior
    const results = await aiCrawler(configPath);

    console.log('🎉 Crawling completed!');
    console.log(`📊 Summary:`);
    console.log(`   • Products found: ${results.products.length}`);
    console.log(`   • Pages processed: ${results.pages_processed}`);
    console.log(`   • Total nodes discovered: ${results.total_nodes}`);
    console.log(`   • Domain: ${results.domain}`);

    // Display first few products
    if (results.products.length > 0) {
      console.log('\n🛍️ Sample products:');
      results.products.slice(0, 5).forEach((product, index) => {
        console.log(`   ${index + 1}. ${product.productName}`);
        console.log(`      → ${product.url}`);
      });

      if (results.products.length > 5) {
        console.log(`   ... and ${results.products.length - 5} more products`);
      }
    }

  } catch (error) {
    console.error('❌ Crawler failed:', error.message);
    process.exit(1);
  }
}

// Run the application
main().catch(console.error);
```

### Your Project Structure

After integration, your TypeScript project should look like this:

```
your-typescript-project/
├── src/
│   ├── crawler-service.ts    # Your crawler service wrapper
│   ├── main.ts              # Your main application
│   └── config.json          # Crawler configuration
├── .env                     # Your environment variables (CLAUDE_API_KEY)
├── package.json            # Your project dependencies
└── *.json                  # Generated crawler results
```

## Configuration

### Config File Format

The TypeScript wrapper uses the same configuration format as the Python main.py:

```json
{
  "url": "https://target-website.com",           // Required: Target website URL
  "delay": 1.5,                                 // Optional: Delay between requests (default: 1.0)
  "max_pages": 100,                            // Optional: Max pages to crawl (default: 50)
  "output": "results.json",                    // Optional: Output file path (auto-generated if omitted)
  "ai_provider": "anthropic",                  // Optional: AI provider (default: anthropic)
  "ai_model": "claude-sonnet-4-20250514"      // Optional: AI model (default: claude-sonnet-4-20250514)
}
```

#### Supported AI Models

**Anthropic (ai_provider: "anthropic")**
- `claude-sonnet-4-20250514` (default - best balance of speed and quality)
- `claude-3-opus-20240229` (highest quality, slower)
- `claude-3-sonnet-20240229` (good balance)
- `claude-3-haiku-20240307` (fastest, most cost-effective)

**OpenAI (ai_provider: "openai")**
- `gpt-4` (high quality)
- `gpt-3.5-turbo` (fast and cost-effective)

**Google (ai_provider: "google")**
- `gemini-pro` (Google's flagship model)

### Environment Variables

Required in your `.env` file (depending on which AI provider you use):

- `CLAUDE_API_KEY` - Your Claude API key from [Anthropic Console](https://console.anthropic.com/) (required for Anthropic models)
- `OPENAI_API_KEY` - Your OpenAI API key from [OpenAI Platform](https://platform.openai.com/) (required for OpenAI models)
- `GOOGLE_API_KEY` - Your Google API key from [Google AI Studio](https://makersuite.google.com/) (required for Google models)

## API Reference

### aiCrawler Function

```typescript
function aiCrawler(configPath: string): Promise<CrawlerResult>
```

**Parameters:**
- `configPath` - Path to JSON configuration file

**Returns:**
- `Promise<CrawlerResult>` - The crawling results

### CrawlerResult Interface

```typescript
interface CrawlerResult {
  products: Array<{
    productName: string;
    url: string;
  }>;
  pages_processed: number;
  total_nodes: number;
  base_url: string;
  domain: string;
}
```

## Requirements

- Node.js ≥ 16.0.0
- Python ≥ 3.8
- AI API key (Claude, OpenAI, or Google)

## 🌟 Key Features

- 🤖 **AI-guided crawling** - Intelligent page prioritization using AI
- 🔄 **Dynamic content support** - Handles pagination, load-more buttons, tabs, accordions, infinite scroll
- 📊 **Simple integration** - Single function call just like Python main.py
- 🛡️ **Robust error handling** - Comprehensive error recovery and reporting
- 📁 **Structured JSON output** - Clean, consistent data format
- ⚙️ **Configurable parameters** - Customizable delays, page limits, and output options
- 🚀 **Easy TypeScript integration** - Drop-in solution for Node.js projects
- 🔒 **Secure API key management** - Environment variable configuration

## Example Output

```json
{
  "products": [
    {
      "productName": "Example Product 1",
      "url": "https://example.com/product1"
    }
  ],
  "pages_processed": 45,
  "total_nodes": 120,
  "base_url": "https://example.com",
  "domain": "example.com"
}
```

## Error Handling

The crawler includes comprehensive error handling:

```typescript
try {
  const results = await aiCrawler('./config.json');
} catch (error) {
  if (error.message.includes("CLAUDE_API_KEY")) {
    console.error("Please set CLAUDE_API_KEY in your .env file");
  } else if (error.message.includes("Config file not found")) {
    console.error("Config file does not exist");
  } else {
    console.error("Crawler failed:", error.message);
  }
}
```

## Troubleshooting

**"CLAUDE_API_KEY environment variable is required"**
- Create `.env` file with `CLAUDE_API_KEY=your_key_here`

**"Config file not found"**
- Ensure the config file path exists and is accessible
- Use absolute paths or paths relative to your working directory

**"Failed to start Python crawler process"**
- Run `pip install -e .` from the cloned repository root
- Ensure Python ≥ 3.8: `python --version`

**Installation issues**
- Update pip: `pip install --upgrade pip`
- Check file permissions for the config file