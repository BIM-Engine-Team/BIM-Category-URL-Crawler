import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class PageAnalyzer:
    def __init__(self):
        self.link_patterns = {
            'navigation': ['nav', 'navigation', 'menu'],
            'content': ['main', 'content', 'article'],
            'footer': ['footer', 'foot'],
            'sidebar': ['sidebar', 'aside']
        }

    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []

            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if href and not href.startswith('#'):
                    absolute_url = urljoin(base_url, href)
                    if self._is_valid_url(absolute_url, base_url):
                        links.append(absolute_url)

            return list(set(links))  # Remove duplicates

        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
            return []

    def extract_page_metadata(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract metadata from page content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            metadata = {
                'title': '',
                'description': '',
                'keywords': [],
                'headings': [],
                'images': [],
                'forms': [],
                'text_content': ''
            }

            # Title
            title_tag = soup.find('title')
            metadata['title'] = title_tag.get_text().strip() if title_tag else ''

            # Meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content', '').strip()

            # Meta keywords
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag:
                keywords_text = keywords_tag.get('content', '')
                metadata['keywords'] = [k.strip() for k in keywords_text.split(',')]

            # Headings
            for level in range(1, 7):
                headings = soup.find_all(f'h{level}')
                for heading in headings:
                    metadata['headings'].append({
                        'level': level,
                        'text': heading.get_text().strip()
                    })

            # Images
            images = soup.find_all('img', src=True)
            for img in images:
                src = img.get('src')
                alt = img.get('alt', '')
                metadata['images'].append({
                    'src': urljoin(url, src),
                    'alt': alt
                })

            # Forms
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                method = form.get('method', 'get').lower()
                metadata['forms'].append({
                    'action': urljoin(url, action) if action else '',
                    'method': method
                })

            # Text content (cleaned)
            for script in soup(["script", "style"]):
                script.decompose()
            metadata['text_content'] = soup.get_text()

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {e}")
            return {}

    def classify_links_by_section(
        self,
        html_content: str,
        base_url: str
    ) -> Dict[str, List[str]]:
        """
        Classify links by page section (navigation, content, footer, etc.)
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            classified_links = {
                'navigation': [],
                'content': [],
                'footer': [],
                'sidebar': [],
                'other': []
            }

            # Find links by section
            for section_name, selectors in self.link_patterns.items():
                for selector in selectors:
                    # Try by tag name
                    sections = soup.find_all(selector)
                    # Try by class name
                    sections.extend(soup.find_all(attrs={'class': re.compile(selector, re.I)}))
                    # Try by id
                    sections.extend(soup.find_all(attrs={'id': re.compile(selector, re.I)}))

                    for section in sections:
                        links = section.find_all('a', href=True)
                        for link in links:
                            href = link['href'].strip()
                            if href and not href.startswith('#'):
                                absolute_url = urljoin(base_url, href)
                                if self._is_valid_url(absolute_url, base_url):
                                    classified_links[section_name].append(absolute_url)

            # Find remaining links not in specific sections
            all_links = set()
            for section_links in classified_links.values():
                all_links.update(section_links)

            page_links = self.extract_links(html_content, base_url)
            other_links = [link for link in page_links if link not in all_links]
            classified_links['other'] = other_links

            # Remove duplicates
            for section in classified_links:
                classified_links[section] = list(set(classified_links[section]))

            return classified_links

        except Exception as e:
            logger.error(f"Error classifying links from {base_url}: {e}")
            return {'navigation': [], 'content': [], 'footer': [], 'sidebar': [], 'other': []}

    def analyze_content_structure(self, html_content: str) -> Dict[str, Any]:
        """
        Analyze the overall structure of page content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            structure = {
                'has_navigation': False,
                'has_sidebar': False,
                'has_footer': False,
                'content_sections': 0,
                'list_items': 0,
                'table_count': 0,
                'form_count': 0,
                'estimated_content_depth': 0
            }

            # Check for major page sections
            nav_elements = soup.find_all(['nav']) + soup.find_all(attrs={'class': re.compile('nav', re.I)})
            structure['has_navigation'] = len(nav_elements) > 0

            sidebar_elements = soup.find_all(attrs={'class': re.compile('sidebar|aside', re.I)})
            structure['has_sidebar'] = len(sidebar_elements) > 0

            footer_elements = soup.find_all(['footer']) + soup.find_all(attrs={'class': re.compile('footer', re.I)})
            structure['has_footer'] = len(footer_elements) > 0

            # Content analysis
            main_content = soup.find('main') or soup.find(attrs={'class': re.compile('content|main', re.I)})
            if main_content:
                structure['content_sections'] = len(main_content.find_all(['section', 'article', 'div']))

            # Lists and tables
            structure['list_items'] = len(soup.find_all(['ul', 'ol']))
            structure['table_count'] = len(soup.find_all('table'))
            structure['form_count'] = len(soup.find_all('form'))

            # Estimate content hierarchy depth
            max_depth = 0
            for element in soup.find_all():
                depth = len(list(element.parents))
                max_depth = max(max_depth, depth)
            structure['estimated_content_depth'] = max_depth

            return structure

        except Exception as e:
            logger.error(f"Error analyzing content structure: {e}")
            return {}

    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """
        Check if URL is valid for crawling
        """
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)

            # Must be same domain
            if parsed_url.netloc != parsed_base.netloc:
                return False

            # Skip common non-content URLs
            skip_patterns = [
                r'\.(?:jpg|jpeg|png|gif|bmp|svg|ico|css|js|pdf|zip|rar|exe)$',
                r'mailto:',
                r'tel:',
                r'javascript:',
                r'#',
                r'\?.*download',
                r'/download/'
            ]

            url_lower = url.lower()
            for pattern in skip_patterns:
                if re.search(pattern, url_lower):
                    return False

            return True

        except Exception:
            return False

    def extract_product_indicators(self, html_content: str) -> Dict[str, Any]:
        """
        Extract indicators that suggest product/catalog content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text().lower()

            indicators = {
                'has_prices': bool(re.search(r'\$[\d,]+\.?\d*', text_content)),
                'has_product_numbers': bool(re.search(r'(?:sku|model|part)\s*:?\s*[\w\d-]+', text_content)),
                'has_specifications': bool(re.search(r'(?:spec|dimension|size|weight|material)', text_content)),
                'has_add_to_cart': 'add to cart' in text_content or 'add cart' in text_content,
                'has_product_images': len(soup.find_all('img', alt=re.compile('product', re.I))) > 0,
                'catalog_indicators': []
            }

            # Architecture-specific product indicators
            arch_indicators = [
                'doors', 'windows', 'roofing', 'flooring', 'siding',
                'tiles', 'lumber', 'hardware', 'fixtures', 'materials'
            ]

            for indicator in arch_indicators:
                if indicator in text_content:
                    indicators['catalog_indicators'].append(indicator)

            return indicators

        except Exception as e:
            logger.error(f"Error extracting product indicators: {e}")
            return {}