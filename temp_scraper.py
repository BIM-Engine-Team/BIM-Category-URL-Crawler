#!/usr/bin/env python3
"""
Temporary web scraper using BeautifulSoup
Usage: python temp_scraper.py <url>
"""

import requests
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime

def scrape_website(url, output_dir="temp_output"):
    """Scrape a website and save the content"""

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Send GET request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract basic information
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title"

        # Get all text content
        text_content = soup.get_text(separator='\n', strip=True)

        # Extract all links
        links = []
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(url, link['href'])
            links.append({
                'text': link.get_text().strip(),
                'url': absolute_url
            })

        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            absolute_url = urljoin(url, img['src'])
            images.append({
                'alt': img.get('alt', ''),
                'src': absolute_url
            })

        # Create output data
        scraped_data = {
            'url': url,
            'title': title_text,
            'scraped_at': datetime.now().isoformat(),
            'links_count': len(links),
            'images_count': len(images),
            'links': links,
            'images': images,
            'text_content': text_content
        }

        # Save raw HTML
        domain = urlparse(url).netloc.replace('.', '_')
        html_filename = f"{output_dir}/{domain}_raw.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))

        # Save extracted data as JSON
        json_filename = f"{output_dir}/{domain}_data.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)

        # Save text content
        text_filename = f"{output_dir}/{domain}_text.txt"
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title_text}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Scraped at: {scraped_data['scraped_at']}\n")
            f.write("="*50 + "\n\n")
            f.write(text_content)

        print(f"✅ Successfully scraped {url}")
        print(f"📁 Output saved to {output_dir}/")
        print(f"   - Raw HTML: {html_filename}")
        print(f"   - Structured data: {json_filename}")
        print(f"   - Text content: {text_filename}")
        print(f"📊 Found {len(links)} links and {len(images)} images")

        return scraped_data

    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing {url}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python temp_scraper.py <url>")
        print("Example: python temp_scraper.py https://example.com")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    scrape_website(url)