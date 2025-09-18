"""
Dynamic loading handling for web pages with various interaction types.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Set
from playwright.async_api import async_playwright, Page, Browser
from urllib.parse import urljoin

from .models import LinkInfo
from .utils import is_same_domain, extract_link_info_from_html


class DynamicLoadingHandler:
    """Handler for various types of dynamic loading on web pages."""

    def __init__(self, domain: str, delay: float = 1.0):
        """
        Initialize the dynamic loading handler.

        Args:
            domain: The target domain to stay within
            delay: Delay between actions in seconds
        """
        self.domain = domain
        self.delay = delay
        self.logger = logging.getLogger(__name__)

    async def check_and_exhaust_dynamic_loading(
        self,
        url: str,
        children_info: List[LinkInfo],
        discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """
        Check if a page has dynamic loading and exhaust all possible content.

        Args:
            url: The page URL to check
            children_info: List of already discovered child links
            discovered_urls: Set of already discovered URLs to avoid duplicates

        Returns:
            List of additional LinkInfo objects found through dynamic loading
        """
        self.logger.info(f"[DYNAMIC_LOADING] Checking dynamic loading for {url}")

        # Filter children info to only include relevant fields for AI analysis
        pruned_children = []
        for link_info in children_info:
            pruned_children.append({
                "id": link_info.id,
                "relative_path": link_info.relative_path,
                "link_tag": link_info.link_tag,
                "link_text": link_info.link_text
            })

        # Check with AI if there's dynamic loading
        dynamic_elements = await self._check_with_ai(pruned_children)

        additional_links = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(self.delay)

                # Handle AI-detected dynamic loading elements
                if dynamic_elements:
                    for element_info in dynamic_elements:
                        element_id = element_info.get("id")
                        trigger_type = element_info.get("triggerType")

                        if element_id != -1 and trigger_type:
                            self.logger.info(f"[DYNAMIC_LOADING] Processing {trigger_type} for element ID {element_id}")
                            element_links = await self._exhaust_dynamic_element(
                                page, element_id, trigger_type, children_info, url, discovered_urls
                            )
                            additional_links.extend(element_links)

                # Always check for infinite scroll
                scroll_links = await self._check_infinite_scroll(page, url, discovered_urls)
                additional_links.extend(scroll_links)

            except Exception as e:
                self.logger.error(f"[DYNAMIC_LOADING] Error processing {url}: {e}")
            finally:
                await browser.close()

        self.logger.info(f"[DYNAMIC_LOADING] Found {len(additional_links)} additional links from dynamic loading")
        return additional_links

    async def _check_with_ai(self, pruned_children: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use AI to determine if the page has dynamic loading elements.

        Args:
            pruned_children: List of pruned link information for AI analysis

        Returns:
            List of dynamic loading elements with their trigger types
        """
        try:
            # Import AI middleware
            try:
                from src.util.ai_client.ai_middleware import send_ai_prompt
            except ImportError:
                from util.ai_client.ai_middleware import send_ai_prompt

            system_prompt = (
                "You are an architect. You want to find the product information from a supplier's website. "
                "You are clicking the button to go to the production description page."
            )

            instruction_prompt = f"""On this page, you found multiple links to product description pages. According to the UI elements on this page, do you think the page uses dynamic loading? If yes, output the element's id and tell its trigger type (select one from: Pagination, Load More, Tabs, Accordions, Expanders), if no, you answer with {{"id": -1}}.

Here is the list of elements:
{pruned_children}"""

            output_structure_prompt = """Please format your response as JSON with the following structure:
[
    {"id": 3, "triggerType": "Pagination"},
    {"id": 7, "triggerType": "Load More"},
    {"id": -1}
]

IMPORTANT:
- If no dynamic loading is detected, return [{"id": -1}]
- If dynamic loading is found, provide the element ID and trigger type
- Valid trigger types are: Pagination, Load More, Tabs, Accordions, Expanders"""

            ai_response = send_ai_prompt(
                system_prompt=system_prompt,
                instruction_prompt=instruction_prompt,
                output_structure_prompt=output_structure_prompt,
                max_tokens=1000
            )

            # Parse AI response
            import json
            dynamic_elements = []

            try:
                start_idx = ai_response.find('[')
                end_idx = ai_response.rfind(']') + 1

                if start_idx != -1 and end_idx > start_idx:
                    json_str = ai_response[start_idx:end_idx]
                    # Clean up the JSON string
                    json_str = json_str.strip()
                    if json_str:
                        dynamic_elements = json.loads(json_str)
                        # Filter out non-dynamic elements
                        return [elem for elem in dynamic_elements if elem.get("id", -1) != -1]
                    else:
                        self.logger.warning(f"[DYNAMIC_LOADING] Empty JSON string extracted from AI response")
                else:
                    self.logger.warning(f"[DYNAMIC_LOADING] No JSON array found in AI response: {ai_response[:200]}...")
            except json.JSONDecodeError as json_error:
                self.logger.error(f"[DYNAMIC_LOADING] JSON decode error: {json_error}. Response fragment: {ai_response[start_idx:end_idx] if 'start_idx' in locals() else 'N/A'}")
            except Exception as parse_error:
                self.logger.error(f"[DYNAMIC_LOADING] Response parsing error: {parse_error}")

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] AI check failed: {e}")

        return []

    async def _exhaust_dynamic_element(
        self,
        page: Page,
        element_id: int,
        trigger_type: str,
        children_info: List[LinkInfo],
        base_url: str,
        discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """
        Exhaust a specific dynamic loading element.

        Args:
            page: Playwright page object
            element_id: ID of the element to interact with
            trigger_type: Type of dynamic loading (Pagination, Load More, etc.)
            children_info: Original children info to find the target element
            base_url: Base URL for resolving relative links
            discovered_urls: Set of already discovered URLs

        Returns:
            List of additional LinkInfo objects
        """
        additional_links = []

        try:
            # Find the target element from children_info
            target_element = None
            for link_info in children_info:
                if link_info.id == element_id:
                    target_element = link_info
                    break

            if not target_element:
                self.logger.warning(f"[DYNAMIC_LOADING] Element with ID {element_id} not found in children_info")
                return additional_links

            if trigger_type == "Pagination":
                additional_links = await self._handle_pagination(page, target_element, base_url, discovered_urls)
            elif trigger_type == "Load More":
                additional_links = await self._handle_load_more(page, target_element, base_url, discovered_urls)
            elif trigger_type == "Tabs":
                additional_links = await self._handle_tabs(page, target_element, base_url, discovered_urls)
            elif trigger_type == "Accordions":
                additional_links = await self._handle_accordions(page, target_element, base_url, discovered_urls)
            elif trigger_type == "Expanders":
                additional_links = await self._handle_expanders(page, target_element, base_url, discovered_urls)

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Error handling {trigger_type} element {element_id}: {e}")

        return additional_links

    async def _find_element_by_target(self, page: Page, target_element: LinkInfo):
        """
        Find the actual DOM element using the target_element information.

        Args:
            page: Playwright page object
            target_element: LinkInfo object containing element details

        Returns:
            Playwright element handle or None
        """
        try:
            # Try to find by link text first
            if target_element.link_text:
                element = await page.query_selector(f"text='{target_element.link_text}'")
                if element:
                    return element

            # Try to find by href
            if target_element.relative_path:
                element = await page.query_selector(f"a[href*='{target_element.relative_path}']")
                if element:
                    return element

            # Try to find by partial href
            href_parts = target_element.relative_path.split('/')
            for part in href_parts:
                if part and len(part) > 3:  # Only use meaningful parts
                    element = await page.query_selector(f"a[href*='{part}']")
                    if element:
                        return element

        except Exception as e:
            self.logger.debug(f"[DYNAMIC_LOADING] Error finding element: {e}")

        return None

    async def _handle_pagination(self, page: Page, target_element: LinkInfo, base_url: str, discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle pagination dynamic loading using the target element."""
        additional_links = []

        try:
            # First try to use the target element directly
            current_element = await self._find_element_by_target(page, target_element)

            max_pages = 10  # Limit to prevent infinite loops
            page_count = 0

            while page_count < max_pages and current_element:
                # Click the pagination element
                if await current_element.is_visible():
                    await current_element.click()
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(self.delay)

                    # Extract new links from the updated page
                    html_content = await page.content()
                    new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links))

                    # Filter for valid, in-domain links
                    valid_links = []
                    for link_info in new_links:
                        if (link_info.url not in discovered_urls and
                            is_same_domain(link_info.url, self.domain)):
                            valid_links.append(link_info)
                            discovered_urls.add(link_info.url)

                    additional_links.extend(valid_links)
                    page_count += 1

                    if not valid_links:  # No new links found
                        break

                    # Try to find the next pagination element
                    current_element = await self._find_element_by_target(page, target_element)
                else:
                    break

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Pagination handling error: {e}")

        return additional_links

    async def _handle_load_more(self, page: Page, target_element: LinkInfo, base_url: str, discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle 'Load More' dynamic loading using the target element."""
        additional_links = []

        try:
            current_element = await self._find_element_by_target(page, target_element)
            max_clicks = 20  # Limit to prevent infinite loops
            click_count = 0

            while click_count < max_clicks and current_element:
                if await current_element.is_visible():
                    await current_element.click()
                    await page.wait_for_timeout(2000)  # Wait for content to load
                    await asyncio.sleep(self.delay)

                    # Extract new links
                    html_content = await page.content()
                    new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links))

                    # Filter for valid links
                    valid_links = []
                    for link_info in new_links:
                        if (link_info.url not in discovered_urls and
                            is_same_domain(link_info.url, self.domain)):
                            valid_links.append(link_info)
                            discovered_urls.add(link_info.url)

                    additional_links.extend(valid_links)
                    click_count += 1

                    if not valid_links:  # No new links found
                        break

                    # Try to find the load more button again (it might have moved)
                    current_element = await self._find_element_by_target(page, target_element)
                else:
                    break

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Load More handling error: {e}")

        return additional_links

    async def _handle_tabs(self, page: Page, target_element: LinkInfo, base_url: str, discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle tabs dynamic loading using the target element."""
        additional_links = []

        try:
            # Click the target tab element
            tab_element = await self._find_element_by_target(page, target_element)

            if tab_element and await tab_element.is_visible():
                await tab_element.click()
                await page.wait_for_timeout(1000)
                await asyncio.sleep(self.delay)

                # Extract links from tab content
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links))

                # Filter for valid links
                for link_info in new_links:
                    if (link_info.url not in discovered_urls and
                        is_same_domain(link_info.url, self.domain)):
                        additional_links.append(link_info)
                        discovered_urls.add(link_info.url)

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Tab handling error: {e}")

        return additional_links

    async def _handle_accordions(self, page: Page, target_element: LinkInfo, base_url: str, discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle accordion dynamic loading using the target element."""
        additional_links = []

        try:
            # Click the target accordion element
            accordion_element = await self._find_element_by_target(page, target_element)

            if accordion_element and await accordion_element.is_visible():
                await accordion_element.click()
                await page.wait_for_timeout(1000)
                await asyncio.sleep(self.delay)

                # Extract links from expanded content
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links))

                # Filter for valid links
                for link_info in new_links:
                    if (link_info.url not in discovered_urls and
                        is_same_domain(link_info.url, self.domain)):
                        additional_links.append(link_info)
                        discovered_urls.add(link_info.url)

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Accordion handling error: {e}")

        return additional_links

    async def _handle_expanders(self, page: Page, target_element: LinkInfo, base_url: str, discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle expander dynamic loading using the target element."""
        additional_links = []

        try:
            # Click the target expander element
            expander_element = await self._find_element_by_target(page, target_element)

            if expander_element and await expander_element.is_visible():
                await expander_element.click()
                await page.wait_for_timeout(1000)
                await asyncio.sleep(self.delay)

                # Extract links from expanded content
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links))

                # Filter for valid links
                for link_info in new_links:
                    if (link_info.url not in discovered_urls and
                        is_same_domain(link_info.url, self.domain)):
                        additional_links.append(link_info)
                        discovered_urls.add(link_info.url)

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Expander handling error: {e}")

        return additional_links

    async def _check_infinite_scroll(self, page: Page, base_url: str, discovered_urls: Set[str]) -> List[LinkInfo]:
        """Check for infinite scroll and exhaust content."""
        additional_links = []

        try:
            # Get initial page height
            initial_height = await page.evaluate("document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 10

            while scroll_attempts < max_scrolls:
                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(self.delay * 2)  # Wait for content to load

                # Check if new content loaded
                new_height = await page.evaluate("document.body.scrollHeight")

                if new_height == initial_height:
                    break  # No new content loaded

                # Extract new links from the page
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links))

                # Filter for valid links
                for link_info in new_links:
                    if (link_info.url not in discovered_urls and
                        is_same_domain(link_info.url, self.domain)):
                        additional_links.append(link_info)
                        discovered_urls.add(link_info.url)

                initial_height = new_height
                scroll_attempts += 1

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Infinite scroll check error: {e}")

        return additional_links