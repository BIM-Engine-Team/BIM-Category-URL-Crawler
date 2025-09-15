import aiohttp
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, request_delay: float = 1.5, timeout: int = 30):
        self.request_delay = request_delay
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0

    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get(self, url: str) -> Optional[Dict[str, Any]]:
        if not self.session:
            raise RuntimeError("HTTP client not initialized. Use 'async with' context manager.")

        # Rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        try:
            async with self.session.get(url) as response:
                self.last_request_time = asyncio.get_event_loop().time()

                if response.status == 200:
                    content = await response.text()
                    return {
                        'url': str(response.url),
                        'status': response.status,
                        'content': content,
                        'headers': dict(response.headers)
                    }
                else:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout for URL: {url}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error for URL {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for URL {url}: {e}")
            return None

    @staticmethod
    def normalize_url(url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs"""
        return urljoin(base_url, url)

    @staticmethod
    def get_domain(url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc