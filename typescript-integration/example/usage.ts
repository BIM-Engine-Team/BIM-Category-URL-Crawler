import aiCrawler from '../src/index';
import * as path from 'path';

// Example usage of the simplified AI crawler interface
async function example() {
  try {
    // Path to your config file (same format as Python main.py expects)
    const configPath = path.join(__dirname, 'sample-config.json');

    // Call the crawler with config file path - mirrors Python main.py behavior
    const results = await aiCrawler(configPath);

    console.log('Crawling completed!');
    console.log(`Found ${results.products.length} products`);
    console.log(`Processed ${results.pages_processed} pages`);
    console.log(`Total nodes discovered: ${results.total_nodes}`);

    // Display first few products
    results.products.slice(0, 5).forEach((product, index) => {
      console.log(`${index + 1}. ${product.productName}`);
      console.log(`   URL: ${product.url}`);
    });

  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run the example
example();