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

### Step 4: Integrate into Your TypeScript Project

**Option A: Copy the built package to your project**
```bash
# From your TypeScript project root
cp -r ../bim-category-url-crawler/typescript-integration/dist ./ai-crawler
cp ../bim-category-url-crawler/typescript-integration/package.json ./ai-crawler/
```

**Option B: Install as local dependency**
```bash
# From your TypeScript project root
npm install ../bim-category-url-crawler/typescript-integration
```

### Step 5: Environment Setup

Create a `.env` file in your TypeScript project root:

```env
CLAUDE_API_KEY=your_claude_api_key_here
```

### Step 6: Quick Test

```bash
# Test the installation
node -e "
const { AIWebCrawler } = require('./ai-crawler/dist');
const crawler = new AIWebCrawler();
console.log('✅ AI Crawler loaded successfully!');
"
```

## 💻 Usage in Your TypeScript Project

### Basic Implementation

```typescript
// src/crawler-service.ts
import { AIWebCrawler, CrawlerConfig, CrawlerProgress } from './ai-crawler/dist';
// or if using Option B: import { AIWebCrawler, CrawlerConfig, CrawlerProgress } from 'bim-category-url-crawler';

export class ProductCrawlerService {
  private crawler = new AIWebCrawler();

  async crawlProducts(websiteUrl: string): Promise<any> {
    const config: CrawlerConfig = {
      url: websiteUrl,
      delay: 1.5,           // Delay between requests (seconds)
      maxPages: 100,        // Maximum pages to crawl
      output: `products_${Date.now()}.json`  // Optional: specify output file
    };

    try {
      console.log(`🚀 Starting to crawl: ${websiteUrl}`);

      const results = await this.crawler.crawl(config, (progress: CrawlerProgress) => {
        // Handle real-time progress updates
        switch (progress.type) {
          case 'progress':
            console.log(`📍 ${progress.message}`);
            break;
          case 'error':
            console.error(`❌ ${progress.message}`);
            break;
          case 'complete':
            console.log(`✅ ${progress.message}`);
            break;
        }
      });

      return {
        success: true,
        data: results,
        message: `Found ${results.products.length} products!`
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

### Complete Example Application

```typescript
// src/main.ts
import { ProductCrawlerService } from './crawler-service';

async function main() {
  const crawlerService = new ProductCrawlerService();

  // Example: Crawl Sherwin Williams for paint products
  const result = await crawlerService.crawlProducts('https://www.sherwin-williams.com');

  if (result.success) {
    console.log(`\n🎉 Crawling completed successfully!`);
    console.log(`📊 Summary:`);
    console.log(`   • Products found: ${result.data.products.length}`);
    console.log(`   • Pages processed: ${result.data.pagesProcessed}`);
    console.log(`   • Total nodes discovered: ${result.data.totalNodes}`);
    console.log(`   • Domain: ${result.data.domain}`);

    // Display first few products
    if (result.data.products.length > 0) {
      console.log('\n🛍️ Sample products:');
      result.data.products.slice(0, 5).forEach((product, index) => {
        console.log(`   ${index + 1}. ${product.productName}`);
        console.log(`      → ${product.url}`);
      });

      if (result.data.products.length > 5) {
        console.log(`   ... and ${result.data.products.length - 5} more products`);
      }
    }

  } else {
    console.error(`❌ Crawling failed: ${result.error}`);
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
│   └── main.ts              # Your main application
├── ai-crawler/              # Copied crawler package
│   ├── dist/               # Built TypeScript files
│   └── package.json        # Package metadata
├── .env                    # Your environment variables
├── package.json            # Your project dependencies
└── products_*.json         # Generated crawler results
```

## Configuration

### CrawlerConfig Interface

```typescript
interface CrawlerConfig {
  url: string; // Target website URL
  delay?: number; // Delay between requests (default: 1.5)
  maxPages?: number; // Max pages to crawl (default: 50)
  output?: string; // Output file path (optional)
}
```

### Environment Variables

Required in your `.env` file:

- `CLAUDE_API_KEY` - Your Claude API key from [Anthropic Console](https://console.anthropic.com/)

### Dependencies for Your TypeScript Project

Add these to your `package.json`:

```json
{
  "dependencies": {
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

## API Reference

### AIWebCrawler Class

#### Methods

- `crawl(config, onProgress?)` - Run the crawler
- `checkInstallation()` - Check if Python package is installed
- `installCrawler()` - Install the Python package

#### Progress Callback

```typescript
interface CrawlerProgress {
  type: "progress" | "error" | "complete";
  message: string;
  data?: any;
}
```

## Requirements

- Node.js ≥ 16.0.0
- Python ≥ 3.8
- Claude API key from Anthropic

## 🌟 Key Features

- 🤖 **AI-guided crawling** - Intelligent page prioritization using Claude AI
- 🔄 **Dynamic content support** - Handles pagination, load-more buttons, tabs, accordions, infinite scroll
- 📊 **Real-time progress tracking** - Live updates during crawling process
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
  "pagesProcessed": 45,
  "totalNodes": 120,
  "baseUrl": "https://example.com",
  "domain": "example.com"
}
```

## Error Handling

The crawler includes comprehensive error handling:

```typescript
try {
  const results = await crawler.crawl(config);
} catch (error) {
  if (error.message.includes("CLAUDE_API_KEY")) {
    console.error("Please set CLAUDE_API_KEY in your .env file");
  } else {
    console.error("Crawler failed:", error.message);
  }
}
```

## Troubleshooting

**"CLAUDE_API_KEY environment variable is required"**
- Create `.env` file with `CLAUDE_API_KEY=your_key_here`

**"Python crawler not found"**
- Run `pip install -e .` from the cloned repository root

**Installation issues**
- Check Python ≥ 3.8: `python --version`
- Update pip: `pip install --upgrade pip`
