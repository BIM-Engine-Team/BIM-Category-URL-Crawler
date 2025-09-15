import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import aiohttp
from config.ai_config import AIConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, requests_per_minute: int, requests_per_day: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.minute_requests = []
        self.day_requests = []

    async def wait_if_needed(self):
        now = time.time()

        # Clean old requests
        self.minute_requests = [t for t in self.minute_requests if now - t < 60]
        self.day_requests = [t for t in self.day_requests if now - t < 86400]

        # Check limits
        if len(self.minute_requests) >= self.requests_per_minute:
            wait_time = 60 - (now - self.minute_requests[0])
            await asyncio.sleep(wait_time)

        if len(self.day_requests) >= self.requests_per_day:
            wait_time = 86400 - (now - self.day_requests[0])
            await asyncio.sleep(wait_time)

        # Record request
        self.minute_requests.append(now)
        self.day_requests.append(now)


class AIErrorHandler:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def handle_request(self, request_func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                result = await request_func(*args, **kwargs)
                return result
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise


class BaseAIClient:
    def __init__(self, config: AIConfig):
        self.config = config
        self.config.validate_config()
        self.rate_limiter = RateLimiter(
            config.requests_per_minute,
            config.requests_per_day
        )
        self.error_handler = AIErrorHandler(
            config.max_retries,
            config.retry_delay
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.response_cache: Dict[str, Any] = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt"""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()

    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make request to Claude API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        # Check cache
        cache_key = self._get_cache_key(prompt)
        if self.config.cache_responses and cache_key in self.response_cache:
            cached_response, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                return cached_response

        await self.rate_limiter.wait_if_needed()

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.config.api_key,
            'anthropic-version': '2023-06-01'
        }

        payload = {
            'model': self.config.model,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }

        async with self.session.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                result = await response.json()

                # Cache response
                if self.config.cache_responses:
                    self.response_cache[cache_key] = (result, time.time())

                return result
            else:
                error_text = await response.text()
                raise Exception(f"API request failed with status {response.status}: {error_text}")

    async def query(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query Claude API with error handling"""
        try:
            result = await self.error_handler.handle_request(
                self._make_request, prompt
            )

            # Extract content from Claude response
            if 'content' in result and result['content']:
                content = result['content'][0]['text']

                # Try to parse as JSON if it looks like JSON
                content = content.strip()
                if content.startswith('{') and content.endswith('}'):
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse response as JSON")
                        return {'raw_response': content}

                return {'raw_response': content}

            return None

        except Exception as e:
            logger.error(f"AI query failed: {e}")
            return None