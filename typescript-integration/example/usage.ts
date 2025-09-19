import { AIWebCrawler, CrawlerConfig, CrawlerProgress } from '../src/index';

async function main() {
  const crawler = new AIWebCrawler();

  // Configuration for crawling
  const config: CrawlerConfig = {
    url: 'https://www.sherwin-williams.com',
    delay: 1.5,
    maxPages: 100,
    output: 'products.json'
  };

  try {
    console.log('Starting AI web crawler...');

    // Run crawler with progress callback
    const results = await crawler.crawl(config, (progress: CrawlerProgress) => {
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

    // Display results
    console.log('\n🎉 Crawling completed!');
    console.log(`📊 Summary:`);
    console.log(`   • Products found: ${results.products.length}`);
    console.log(`   • Pages processed: ${results.pagesProcessed}`);
    console.log(`   • Total nodes discovered: ${results.totalNodes}`);
    console.log(`   • Domain: ${results.domain}`);

    // Show first few products
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
    console.error('❌ Crawler failed:', error);
    process.exit(1);
  }
}

// Run the example
if (require.main === module) {
  main().catch(console.error);
}