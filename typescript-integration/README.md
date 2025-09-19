# AI Product Category Crawler - TypeScript Integration

TypeScript/Node.js wrapper for the AI-guided product category crawler Python package.

## Installation

1. **Install the npm package:**
   ```bash
   npm install ai-product-category-crawler
   ```

2. **Install Python dependencies:**
   ```bash
   pip install ai-product-category-crawler
   ```

3. **Set up environment variables:**

   Create a `.env` file in your project root:
   ```env
   CLAUDE_API_KEY=your_claude_api_key_here
   ```

## Usage

```typescript
import { AIWebCrawler, CrawlerConfig } from 'ai-product-category-crawler';

const crawler = new AIWebCrawler();

const config: CrawlerConfig = {
  url: 'https://example.com',
  delay: 1.5,           // Delay between requests (seconds)
  maxPages: 100,        // Maximum pages to crawl
  output: 'results.json' // Optional: specify output file
};

// Run crawler with progress tracking
const results = await crawler.crawl(config, (progress) => {
  console.log(progress.message);
});

console.log(`Found ${results.products.length} products`);
```

## Configuration

### CrawlerConfig Interface

```typescript
interface CrawlerConfig {
  url: string;          // Target website URL
  delay?: number;       // Delay between requests (default: 1.5)
  maxPages?: number;    // Max pages to crawl (default: 50)
  output?: string;      // Output file path (optional)
}
```

### Environment Variables

Required in your `.env` file:
- `CLAUDE_API_KEY` - Your Claude API key from Anthropic

## API Reference

### AIWebCrawler Class

#### Methods

- `crawl(config, onProgress?)` - Run the crawler
- `checkInstallation()` - Check if Python package is installed
- `installCrawler()` - Install the Python package

#### Progress Callback

```typescript
interface CrawlerProgress {
  type: 'progress' | 'error' | 'complete';
  message: string;
  data?: any;
}
```

## Requirements

- Node.js ≥ 16.0.0
- Python ≥ 3.8
- Claude API key from Anthropic

## Features

- 🤖 AI-guided crawling for intelligent page prioritization
- 🔄 Dynamic content support (pagination, load more, tabs, etc.)
- 📊 Real-time progress tracking
- 🛡️ Error handling and recovery
- 📁 Structured JSON output
- ⚙️ Configurable crawling parameters

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
  if (error.message.includes('CLAUDE_API_KEY')) {
    console.error('Please set CLAUDE_API_KEY in your .env file');
  } else {
    console.error('Crawler failed:', error.message);
  }
}
```

## Support

- Check that Python dependencies are installed
- Verify your Claude API key is valid
- Ensure the target website is accessible
- Review crawler logs for detailed error information