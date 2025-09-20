"""
Dynamic loading handling for web pages with various interaction types.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Set
from playwright.async_api import async_playwright, Page, Browser
from urllib.parse import urljoin

from .models import LinkInfo, DynamicElementInfo
from .utils import is_same_domain, extract_link_info_from_html, extract_dynamic_elements


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
        discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """
        Check if a page has dynamic loading and exhaust all possible content.

        Args:
            url: The page URL to check
            discovered_urls: Set of already discovered URLs to avoid duplicates

        Returns:
            List of additional LinkInfo objects found through dynamic loading
        """
        self.logger.info(f"[DYNAMIC_LOADING] Checking dynamic loading for {url}")

        # Extract dynamic elements separately from links using requests (fast)
        try:
            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            dynamic_element_candidates = extract_dynamic_elements(url, session)
            self.logger.info(f"[DYNAMIC_LOADING] Found {len(dynamic_element_candidates)} potential dynamic elements")
        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Error extracting dynamic elements: {e}")
            dynamic_element_candidates = []

        # Check with AI if there's dynamic loading among these candidates
        dynamic_elements = await self._check_with_ai(dynamic_element_candidates)

        additional_links = []
        # Create an empty set to track URLs discovered during this dynamic loading session
        # This prevents re-discovering the same URLs within this function call
        session_discovered_urls = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Use domcontentloaded for faster initial load, then wait for specific content
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(self.delay)

                # Handle AI-detected dynamic loading elements
                if dynamic_elements:
                    for element_info in dynamic_elements:
                        element_id = element_info.get("id")
                        trigger_type = element_info.get("triggerType")

                        if element_id != -1 and trigger_type:
                            # Find element details for logging
                            target_element = None
                            for elem in dynamic_element_candidates:
                                if elem.id == element_id:
                                    target_element = elem
                                    break

                            element_text = target_element.text_content[:100] if target_element and target_element.text_content else "No text"
                            self.logger.info(f"[DYNAMIC_LOADING] ⚡ Starting exhaustion of {trigger_type} element")
                            self.logger.info(f"[DYNAMIC_LOADING] 📝 Element ID {element_id} - Text: '{element_text}'")
                            self.logger.info(f"[DYNAMIC_LOADING] 🔍 Element details: tag={target_element.tag_name if target_element else 'unknown'}, classes='{target_element.class_names if target_element else 'none'}'")

                            element_links = await self._exhaust_dynamic_element(
                                page, element_id, trigger_type, dynamic_element_candidates, url, discovered_urls, session_discovered_urls
                            )

                            self.logger.info(f"[DYNAMIC_LOADING] ✅ Completed exhaustion of {trigger_type} element - Found {len(element_links)} new links")
                            additional_links.extend(element_links)

                # Always check for infinite scroll
                self.logger.info(f"[DYNAMIC_LOADING] 🔄 Starting infinite scroll detection")
                scroll_links = await self._check_infinite_scroll(page, url, discovered_urls, session_discovered_urls)
                self.logger.info(f"[DYNAMIC_LOADING] 📜 Infinite scroll complete: Found {len(scroll_links)} additional links")
                additional_links.extend(scroll_links)

            except Exception as e:
                self.logger.error(f"[DYNAMIC_LOADING] Error processing {url}: {e}")
            finally:
                await browser.close()

        self.logger.info(f"[DYNAMIC_LOADING] Found {len(additional_links)} additional links from dynamic loading")
        return additional_links

    async def _check_with_ai(self, dynamic_element_candidates: List[DynamicElementInfo]) -> List[Dict[str, Any]]:
        """
        Use AI to determine if the page has dynamic loading elements.

        Args:
            dynamic_element_candidates: List of potential dynamic elements for AI analysis

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

            # Convert dynamic element candidates to AI-friendly format
            elements_for_ai = []
            for elem in dynamic_element_candidates:
                elements_for_ai.append({
                    "id": elem.id,
                    "tag": elem.tag_name,
                    "text": elem.text_content,
                    "classes": elem.class_names,
                    "element_id": elem.element_id,
                    "onclick": elem.onclick_handler,
                    "parent": elem.parent_tag,
                    "aria_label": elem.aria_label
                })

            instruction_prompt = f"""On this page, you found potential interactive elements that might trigger dynamic loading of additional content (like more products). Analyze these UI elements and determine if any of them are dynamic loading triggers.

If you find dynamic loading elements, output their ID and trigger type. If no dynamic loading is detected, return "[]" only.

Here is the list of interactive elements found on the page:
{elements_for_ai}

Look for elements that might:
- Load more products/items (buttons with text like "Load More", "Show More", "View More")
- Navigate between pages (pagination buttons, "Next", "Previous")
- Switch between different content sections (tabs, accordions)
- Expand content sections (expandable areas, "Show Details")"""

            output_structure_prompt = """Please format your response as JSON with the following structure:
[
    {"id": 3, "triggerType": "Pagination"},
    {"id": 7, "triggerType": "Load More"}
]

IMPORTANT:
- If no dynamic loading is detected, return []
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
                        # Log the parsed dynamic loading result
                        self.logger.info(f"[DYNAMIC_LOADING_AI] Parsed JSON: {json.dumps(dynamic_elements)}")
                        # Filter out non-dynamic elements
                        return [elem for elem in dynamic_elements]
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
        dynamic_element_candidates: List[DynamicElementInfo],
        base_url: str,
        discovered_urls: Set[str],
        session_discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """
        Exhaust a specific dynamic loading element.

        Args:
            page: Playwright page object
            element_id: ID of the element to interact with
            trigger_type: Type of dynamic loading (Pagination, Load More, etc.)
            dynamic_element_candidates: List of dynamic element candidates to find the target element
            base_url: Base URL for resolving relative links
            discovered_urls: Set of already discovered URLs
            session_discovered_urls: Set of URLs discovered in this session

        Returns:
            List of additional LinkInfo objects
        """
        additional_links = []

        try:
            # Find the target element from dynamic_element_candidates
            target_element = None
            for elem in dynamic_element_candidates:
                if elem.id == element_id:
                    target_element = elem
                    break

            if not target_element:
                self.logger.warning(f"[DYNAMIC_LOADING] ❌ Element with ID {element_id} not found in dynamic element candidates")
                return additional_links

            element_text = target_element.text_content[:50] if target_element.text_content else "No text"
            self.logger.info(f"[DYNAMIC_LOADING] 🎯 Targeting element: '{element_text}' for {trigger_type} exhaustion")

            if trigger_type == "Pagination":
                self.logger.info(f"[DYNAMIC_LOADING] 📄 Starting pagination handler for element: '{element_text}'")
                additional_links = await self._handle_pagination(page, target_element, base_url, discovered_urls, session_discovered_urls)
            elif trigger_type == "Load More":
                self.logger.info(f"[DYNAMIC_LOADING] 📥 Starting load more handler for element: '{element_text}'")
                additional_links = await self._handle_load_more(page, target_element, base_url, discovered_urls, session_discovered_urls)
            elif trigger_type == "Tabs":
                self.logger.info(f"[DYNAMIC_LOADING] 📋 Starting tabs handler for element: '{element_text}'")
                additional_links = await self._handle_tabs(page, target_element, base_url, discovered_urls, session_discovered_urls)
            elif trigger_type == "Accordions":
                self.logger.info(f"[DYNAMIC_LOADING] 🎵 Starting accordion handler for element: '{element_text}'")
                additional_links = await self._handle_accordions(page, target_element, base_url, discovered_urls, session_discovered_urls)
            elif trigger_type == "Expanders":
                self.logger.info(f"[DYNAMIC_LOADING] 🔽 Starting expander handler for element: '{element_text}'")
                additional_links = await self._handle_expanders(page, target_element, base_url, discovered_urls, session_discovered_urls)

        except Exception as e:
            element_text = target_element.text_content[:50] if 'target_element' in locals() and target_element and target_element.text_content else "unknown element"
            self.logger.error(f"[DYNAMIC_LOADING] ❌ Error handling {trigger_type} element {element_id} ('{element_text}'): {e}")

        return additional_links

    async def _find_element_by_target(self, page: Page, target_element: DynamicElementInfo):
        """
        Find the actual DOM element using the target_element information.

        Args:
            page: Playwright page object
            target_element: DynamicElementInfo object containing element details

        Returns:
            Playwright element handle or None
        """
        try:
            # Try to find by HTML id first (most reliable)
            if target_element.element_id:
                element = await page.query_selector(f"#{target_element.element_id}")
                if element:
                    return element

            # Try to find by text content
            if target_element.text_content:
                # Use contains for partial text match
                element = await page.query_selector(f"{target_element.tag_name}:has-text('{target_element.text_content}')")
                if element:
                    return element

            # Try to find by class names
            if target_element.class_names:
                # Use the first class name as a fallback
                first_class = target_element.class_names.split()[0] if target_element.class_names.split() else ""
                if first_class:
                    element = await page.query_selector(f"{target_element.tag_name}.{first_class}")
                    if element:
                        return element

            # For aria-label
            if target_element.aria_label:
                element = await page.query_selector(f"[aria-label='{target_element.aria_label}']")
                if element:
                    return element

        except Exception as e:
            self.logger.debug(f"[DYNAMIC_LOADING] Error finding element: {e}")

        return None

    async def _handle_pagination(self, page: Page, target_element: DynamicElementInfo, base_url: str, discovered_urls: Set[str], session_discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle pagination dynamic loading using the target element."""
        additional_links = []

        try:
            # First try to use the target element directly
            current_element = await self._find_element_by_target(page, target_element)

            max_pages = 10  # Limit to prevent infinite loops
            page_count = 0
            element_text = target_element.text_content[:50] if target_element.text_content else "No text"

            while page_count < max_pages and current_element:
                # Click the pagination element
                if await current_element.is_visible():
                    self.logger.info(f"[PAGINATION] 🖱️ Stage {page_count + 1}/{max_pages}: Clicking pagination element '{element_text}'")

                    # Get initial content count for comparison
                    initial_links = await page.query_selector_all('a[href]')
                    initial_count = len(initial_links)
                    self.logger.info(f"[PAGINATION] 📊 Current page has {initial_count} links before click")

                    await current_element.click()

                    self.logger.info(f"[PAGINATION] ⏳ Waiting for new content to load...")
                    # Wait for new content to load using multiple strategies
                    await self._wait_for_pagination_content(page, initial_count)
                    await asyncio.sleep(self.delay)

                    # Check final content count
                    final_links = await page.query_selector_all('a[href]')
                    final_count = len(final_links)
                    self.logger.info(f"[PAGINATION] 📈 After click: {final_count} links ({final_count - initial_count:+d})")

                    # Extract new links from the updated page
                    html_content = await page.content()
                    new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                    # Filter for valid, in-domain links
                    valid_links = []
                    for link_info in new_links:
                        if (is_same_domain(link_info.url, self.domain)):
                            valid_links.append(link_info)
                            session_discovered_urls.add(link_info.url)  # Add to session tracker

                    additional_links.extend(valid_links)
                    page_count += 1

                    # Log first 5 links found to verify they're actually new
                    if valid_links:
                        sample_links = valid_links[:5]
                        self.logger.info(f"[PAGINATION] 📋 Sample of new links found:")
                        for i, link in enumerate(sample_links, 1):
                            self.logger.info(f"[PAGINATION]   {i}. {link.url}")

                    self.logger.info(f"[PAGINATION] ✅ Page {page_count}: Found {len(valid_links)} new valid links (Total: {len(additional_links)})")

                    if not valid_links:  # No new links found
                        self.logger.info(f"[PAGINATION] 🛑 No new valid links found, stopping pagination")
                        break

                    # Try to find the next pagination element
                    current_element = await self._find_element_by_target(page, target_element)
                    if not current_element:
                        self.logger.info(f"[PAGINATION] 🔍 Pagination element no longer found, stopping")
                else:
                    self.logger.info(f"[PAGINATION] 👁️ Pagination element not visible, stopping")
                    break

            self.logger.info(f"[PAGINATION] 🏁 Pagination complete: {page_count} pages processed, {len(additional_links)} total links")

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Pagination handling error: {e}")

        return additional_links

    async def _wait_for_pagination_content(self, page: Page, initial_count: int):
        """Wait for pagination content to load using multiple strategies."""
        timeout = 10000
        strategies = [
            # Common pagination content selectors
            '.pagination-content, .page-content, .results, .product-list, .item-list',
            # Loading indicators that should disappear
            '.loading, .spinner, [data-loading="true"]',
            # Generic content containers
            '.content, .main-content, .products, .items',
        ]

        try:
            # Strategy 1: Wait for content containers
            for selector in strategies:
                try:
                    await page.wait_for_selector(selector, timeout=timeout//len(strategies))
                    break
                except:
                    continue

            # Strategy 2: Wait for link count to change
            for _ in range(20):  # Check for 2 seconds
                current_links = await page.query_selector_all('a[href]')
                if len(current_links) > initial_count:
                    break
                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.debug(f"[DYNAMIC_LOADING] Pagination content wait timeout: {e}")
            # Continue anyway - some content might have loaded

    async def _handle_load_more(self, page: Page, target_element: DynamicElementInfo, base_url: str, discovered_urls: Set[str], session_discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle 'Load More' dynamic loading using the target element."""
        additional_links = []

        try:
            current_element = await self._find_element_by_target(page, target_element)
            max_clicks = 20  # Limit to prevent infinite loops
            click_count = 0
            element_text = target_element.text_content[:50] if target_element.text_content else "No text"

            while click_count < max_clicks and current_element:
                if await current_element.is_visible():
                    self.logger.info(f"[LOAD_MORE] 🖱️ Stage {click_count + 1}/{max_clicks}: Clicking load more button '{element_text}'")

                    # Get initial content state for comparison
                    initial_links = await page.query_selector_all('a[href]')
                    initial_count = len(initial_links)
                    self.logger.info(f"[LOAD_MORE] 📊 Current content has {initial_count} links before click")

                    await current_element.click()

                    self.logger.info(f"[LOAD_MORE] ⏳ Waiting for new content to load...")
                    # Wait for new content to load using load-more specific strategies
                    await self._wait_for_load_more_content(page, initial_count)
                    await asyncio.sleep(self.delay)

                    # Check final content count
                    final_links = await page.query_selector_all('a[href]')
                    final_count = len(final_links)
                    self.logger.info(f"[LOAD_MORE] 📈 After click: {final_count} links ({final_count - initial_count:+d})")

                    # Extract new links
                    html_content = await page.content()
                    new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                    # Filter for valid links
                    valid_links = []
                    for link_info in new_links:
                        if (is_same_domain(link_info.url, self.domain)):
                            valid_links.append(link_info)
                            session_discovered_urls.add(link_info.url)  # Add to session tracker

                    additional_links.extend(valid_links)
                    click_count += 1

                    # Log first 5 links found to verify they're actually new
                    if valid_links:
                        sample_links = valid_links[:5]
                        self.logger.info(f"[LOAD_MORE] 📋 Sample of new links found:")
                        for i, link in enumerate(sample_links, 1):
                            self.logger.info(f"[LOAD_MORE]   {i}. {link.url}")

                    self.logger.info(f"[LOAD_MORE] ✅ Click {click_count}: Found {len(valid_links)} new valid links (Total: {len(additional_links)})")

                    if not valid_links:  # No new links found
                        self.logger.info(f"[LOAD_MORE] 🛑 No new valid links found, stopping load more")
                        break

                    # Try to find the load more button again (it might have moved)
                    current_element = await self._find_element_by_target(page, target_element)
                    if not current_element:
                        self.logger.info(f"[LOAD_MORE] 🔍 Load more button no longer found, stopping")
                else:
                    self.logger.info(f"[LOAD_MORE] 👁️ Load more button not visible, stopping")
                    break

            self.logger.info(f"[LOAD_MORE] 🏁 Load more complete: {click_count} clicks processed, {len(additional_links)} total links")

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Load More handling error: {e}")

        return additional_links

    async def _wait_for_load_more_content(self, page: Page, initial_count: int):
        """Wait for load more content to appear using multiple strategies."""
        timeout = 15000
        strategies = [
            # Load more specific selectors
            '.loaded-content, .new-items, [data-loaded="true"], .lazy-loaded',
            # Loading indicators that should appear then disappear
            '.loading:not([style*="display: none"]), .spinner:visible, [data-loading="true"]',
            # Common content containers that get populated
            '.product-grid, .item-container, .results-list, .content-list',
        ]

        try:
            # Strategy 1: Wait for loading indicators to appear then disappear
            try:
                await page.wait_for_selector('.loading, .spinner, [data-loading="true"]', timeout=2000)
                await page.wait_for_selector('.loading:not([style*="display: block"]), .spinner:not([style*="display: block"])', timeout=timeout-2000)
            except:
                pass

            # Strategy 2: Wait for content containers
            for selector in strategies:
                try:
                    await page.wait_for_selector(selector, timeout=timeout//len(strategies))
                    break
                except:
                    continue

            # Strategy 3: Wait for link count to increase
            for _ in range(30):  # Check for 3 seconds
                current_links = await page.query_selector_all('a[href]')
                if len(current_links) > initial_count:
                    break
                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.debug(f"[DYNAMIC_LOADING] Load more content wait timeout: {e}")
            # Continue anyway - some content might have loaded

    async def _handle_tabs(self, page: Page, target_element: DynamicElementInfo, base_url: str, discovered_urls: Set[str], session_discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle tabs dynamic loading using the target element."""
        additional_links = []

        try:
            element_text = target_element.text_content[:50] if target_element.text_content else "No text"
            self.logger.info(f"[TABS] 🖱️ Clicking tab element: '{element_text}'")

            # Click the target tab element
            tab_element = await self._find_element_by_target(page, target_element)

            if tab_element and await tab_element.is_visible():
                await tab_element.click()
                self.logger.info(f"[TABS] ✅ Tab clicked successfully")

                self.logger.info(f"[TABS] ⏳ Waiting for tab content to load...")
                # Wait for tab content to load using tab-specific strategies
                await self._wait_for_tab_content(page)
                await asyncio.sleep(self.delay)

                # Extract links from tab content
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                # Filter for valid links
                valid_links = []
                for link_info in new_links:
                    if (is_same_domain(link_info.url, self.domain)):
                        valid_links.append(link_info)
                        session_discovered_urls.add(link_info.url)  # Add to session tracker
                        additional_links.append(link_info)

                self.logger.info(f"[TABS] ✅ Tab processing complete: Found {len(valid_links)} new valid links")
            else:
                self.logger.warning(f"[TABS] ❌ Tab element not found or not visible")

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Tab handling error: {e}")

        return additional_links

    async def _wait_for_tab_content(self, page: Page):
        """Wait for tab content to become visible using multiple strategies."""
        timeout = 8000
        strategies = [
            # Active tab content selectors
            '.tab-content.active, .tab-pane.active, [aria-hidden="false"]',
            # Tab content by display style
            '.tab-content[style*="display: block"], .tab-pane[style*="display: block"]',
            # Generic visible content
            '.tab-content:not([style*="display: none"]), .tab-pane:not([style*="display: none"])',
        ]

        try:
            # Strategy 1: Wait for active tab content
            for selector in strategies:
                try:
                    await page.wait_for_selector(selector, timeout=timeout//len(strategies))
                    # Additional wait to ensure content is fully loaded
                    await page.wait_for_function(
                        f'document.querySelector("{selector}") && document.querySelector("{selector}").offsetHeight > 0',
                        timeout=2000
                    )
                    return
                except:
                    continue

            # Strategy 2: Wait for any content change (fallback)
            await page.wait_for_timeout(1000)

        except Exception as e:
            self.logger.debug(f"[DYNAMIC_LOADING] Tab content wait timeout: {e}")
            # Continue anyway - tab might have loaded

    async def _handle_accordions(self, page: Page, target_element: DynamicElementInfo, base_url: str, discovered_urls: Set[str], session_discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle accordion dynamic loading using the target element."""
        additional_links = []

        try:
            element_text = target_element.text_content[:50] if target_element.text_content else "No text"
            self.logger.info(f"[ACCORDIONS] 🖱️ Clicking accordion element: '{element_text}'")

            # Click the target accordion element
            accordion_element = await self._find_element_by_target(page, target_element)

            if accordion_element and await accordion_element.is_visible():
                await accordion_element.click()
                self.logger.info(f"[ACCORDIONS] ✅ Accordion clicked successfully")

                self.logger.info(f"[ACCORDIONS] ⏳ Waiting for accordion content to expand...")
                # Wait for accordion content to expand using accordion-specific strategies
                await self._wait_for_accordion_content(page)
                await asyncio.sleep(self.delay)

                # Extract links from expanded content
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                # Filter for valid links
                valid_links = []
                for link_info in new_links:
                    if (is_same_domain(link_info.url, self.domain)):
                        valid_links.append(link_info)
                        session_discovered_urls.add(link_info.url)  # Add to session tracker
                        additional_links.append(link_info)

                self.logger.info(f"[ACCORDIONS] ✅ Accordion processing complete: Found {len(valid_links)} new valid links")
            else:
                self.logger.warning(f"[ACCORDIONS] ❌ Accordion element not found or not visible")

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Accordion handling error: {e}")

        return additional_links

    async def _handle_expanders(self, page: Page, target_element: DynamicElementInfo, base_url: str, discovered_urls: Set[str], session_discovered_urls: Set[str]) -> List[LinkInfo]:
        """Handle expander dynamic loading using the target element."""
        additional_links = []

        try:
            element_text = target_element.text_content[:50] if target_element.text_content else "No text"
            self.logger.info(f"[EXPANDERS] 🖱️ Clicking expander element: '{element_text}'")

            # Click the target expander element
            expander_element = await self._find_element_by_target(page, target_element)

            if expander_element and await expander_element.is_visible():
                await expander_element.click()
                self.logger.info(f"[EXPANDERS] ✅ Expander clicked successfully")

                self.logger.info(f"[EXPANDERS] ⏳ Waiting for expander content to load...")
                # Wait for expander content using same strategy as accordions
                await self._wait_for_accordion_content(page)
                await asyncio.sleep(self.delay)

                # Extract links from expanded content
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                # Filter for valid links
                valid_links = []
                for link_info in new_links:
                    if (is_same_domain(link_info.url, self.domain)):
                        valid_links.append(link_info)
                        session_discovered_urls.add(link_info.url)  # Add to session tracker
                        additional_links.append(link_info)

                self.logger.info(f"[EXPANDERS] ✅ Expander processing complete: Found {len(valid_links)} new valid links")
            else:
                self.logger.warning(f"[EXPANDERS] ❌ Expander element not found or not visible")

        except Exception as e:
            self.logger.error(f"[DYNAMIC_LOADING] Expander handling error: {e}")

        return additional_links

    async def _wait_for_accordion_content(self, page: Page):
        """Wait for accordion/expander content to expand using multiple strategies."""
        timeout = 6000
        strategies = [
            # Expanded state selectors
            '[aria-expanded="true"], .expanded, .open, .accordion-open',
            # Content visibility selectors
            '.accordion-content:not([style*="display: none"]), .expand-content[style*="display: block"]',
            # Height-based selectors (accordions often animate height)
            '.accordion-body[style*="height"], .collapsible-content[style*="max-height"]',
        ]

        try:
            # Strategy 1: Wait for expanded state indicators
            for selector in strategies:
                try:
                    await page.wait_for_selector(selector, timeout=timeout//len(strategies))
                    # Wait for animation to complete
                    await page.wait_for_function(
                        f'document.querySelector("{selector}") && document.querySelector("{selector}").offsetHeight > 20',
                        timeout=2000
                    )
                    return
                except:
                    continue

            # Strategy 2: Generic timeout fallback
            await page.wait_for_timeout(1000)

        except Exception as e:
            self.logger.debug(f"[DYNAMIC_LOADING] Accordion content wait timeout: {e}")
            # Continue anyway - content might have expanded

    async def _check_infinite_scroll(self, page: Page, base_url: str, discovered_urls: Set[str], session_discovered_urls: Set[str]) -> List[LinkInfo]:
        """Advanced infinite scroll detection with multiple strategies."""
        self.logger.info("[INFINITE_SCROLL] 🔍 Starting advanced infinite scroll detection")

        try:
            # Strategy 1: Container-based scrolling
            containers = await self._find_scroll_containers(page)

            # Strategy 2: Content count monitoring
            initial_content = await self._get_content_metrics(page)

            # Strategy 3: Loading indicator detection
            loading_selectors = await self._identify_loading_indicators(page)

            # Strategy 4: Intersection observer simulation
            trigger_zones = await self._find_trigger_zones(page)

            return await self._exhaust_scroll_with_strategies(page, containers, initial_content, loading_selectors, trigger_zones, base_url, discovered_urls, session_discovered_urls)

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Advanced infinite scroll detection error: {e}")
            return []

    async def _find_scroll_containers(self, page: Page) -> List[Dict[str, Any]]:
        """Find potential scroll containers on the page."""
        containers = []

        try:
            # Common scroll container patterns
            container_selectors = [
                '[style*="overflow-y: auto"]',
                '[style*="overflow: auto"]',
                '[style*="overflow-y: scroll"]',
                '[style*="overflow: scroll"]',
                '.scroll-container',
                '.scrollable',
                '.infinite-scroll',
                '.lazy-load-container',
                '[data-scroll]',
                '[data-infinite]'
            ]

            for selector in container_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Check if element is actually scrollable
                        is_scrollable = await element.evaluate('''
                            (el) => {
                                const computedStyle = window.getComputedStyle(el);
                                const overflowY = computedStyle.overflowY;
                                const scrollHeight = el.scrollHeight;
                                const clientHeight = el.clientHeight;
                                return (overflowY === 'auto' || overflowY === 'scroll') && scrollHeight > clientHeight;
                            }
                        ''')

                        if is_scrollable:
                            container_info = {
                                'element': element,
                                'selector': selector,
                                'scrollHeight': await element.evaluate('el => el.scrollHeight'),
                                'clientHeight': await element.evaluate('el => el.clientHeight')
                            }
                            containers.append(container_info)
                    except Exception:
                        continue

            # Also check document body as fallback
            body_scrollable = await page.evaluate('''
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    return Math.max(body.scrollHeight, html.scrollHeight) > Math.max(body.clientHeight, html.clientHeight);
                }
            ''')

            if body_scrollable:
                containers.append({
                    'element': None,  # Use document scrolling
                    'selector': 'document',
                    'scrollHeight': await page.evaluate('() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)'),
                    'clientHeight': await page.evaluate('() => Math.max(document.body.clientHeight, document.documentElement.clientHeight)')
                })

            self.logger.info(f"[INFINITE_SCROLL] Found {len(containers)} scroll containers")

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Error finding scroll containers: {e}")

        return containers

    async def _get_content_metrics(self, page: Page) -> Dict[str, int]:
        """Get initial content metrics for comparison."""
        try:
            metrics = await page.evaluate('''
                () => {
                    return {
                        linkCount: document.querySelectorAll('a[href]').length,
                        imageCount: document.querySelectorAll('img').length,
                        productCount: document.querySelectorAll('[data-product], .product, .item, [class*="product"]').length,
                        cardCount: document.querySelectorAll('.card, [class*="card"]').length,
                        listItemCount: document.querySelectorAll('li, [class*="item"]').length,
                        totalElements: document.querySelectorAll('*').length
                    };
                }
            ''')

            self.logger.info(f"[INFINITE_SCROLL] Initial content metrics: {metrics}")
            return metrics

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Error getting content metrics: {e}")
            return {
                'linkCount': 0,
                'imageCount': 0,
                'productCount': 0,
                'cardCount': 0,
                'listItemCount': 0,
                'totalElements': 0
            }

    async def _identify_loading_indicators(self, page: Page) -> List[str]:
        """Identify loading indicators and patterns on the page."""
        loading_selectors = []

        try:
            # Common loading indicator patterns
            potential_selectors = [
                '.loading',
                '.spinner',
                '.loader',
                '[data-loading]',
                '[class*="loading"]',
                '[class*="spinner"]',
                '[class*="loader"]',
                '.fa-spinner',
                '.fa-circle-o-notch',
                '[data-testid*="loading"]',
                '[aria-label*="loading"]',
                '[aria-label*="Loading"]'
            ]

            for selector in potential_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        loading_selectors.append(selector)
                except Exception:
                    continue

            self.logger.info(f"[INFINITE_SCROLL] Found {len(loading_selectors)} loading indicator patterns")

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Error identifying loading indicators: {e}")

        return loading_selectors

    async def _find_trigger_zones(self, page: Page) -> List[Dict[str, Any]]:
        """Find potential trigger zones that might activate infinite scroll."""
        trigger_zones = []

        try:
            # Look for elements that might be scroll triggers
            trigger_selectors = [
                '.load-more',
                '[data-load-more]',
                '.infinite-scroll-trigger',
                '[data-infinite-trigger]',
                '.sentinel',
                '[data-sentinel]',
                '[id*="trigger"]',
                '[class*="trigger"]'
            ]

            for selector in trigger_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Get element position
                        bounding_box = await element.bounding_box()
                        if bounding_box:
                            trigger_zones.append({
                                'element': element,
                                'selector': selector,
                                'position': bounding_box
                            })
                    except Exception:
                        continue

            self.logger.info(f"[INFINITE_SCROLL] Found {len(trigger_zones)} potential trigger zones")

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Error finding trigger zones: {e}")

        return trigger_zones

    async def _exhaust_scroll_with_strategies(
        self,
        page: Page,
        containers: List[Dict[str, Any]],
        initial_content: Dict[str, int],
        loading_selectors: List[str],
        trigger_zones: List[Dict[str, Any]],
        base_url: str,
        discovered_urls: Set[str],
        session_discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """Exhaust infinite scroll using multiple strategies."""
        additional_links = []
        max_attempts = 15
        attempt = 0

        try:
            # Try each scroll container
            for container in containers:
                if attempt >= max_attempts:
                    break

                self.logger.info(f"[INFINITE_SCROLL] Trying container: {container['selector']}")
                container_links = await self._exhaust_container_scroll(
                    page, container, initial_content, loading_selectors, base_url, discovered_urls, session_discovered_urls
                )
                additional_links.extend(container_links)
                attempt += len(container_links) if container_links else 1

            # Try trigger zones if containers didn't work
            if not additional_links and trigger_zones:
                self.logger.info("[INFINITE_SCROLL] Trying trigger zones")
                for trigger_zone in trigger_zones:
                    if attempt >= max_attempts:
                        break

                    zone_links = await self._exhaust_trigger_zone(
                        page, trigger_zone, initial_content, loading_selectors, base_url, discovered_urls, session_discovered_urls
                    )
                    additional_links.extend(zone_links)
                    attempt += len(zone_links) if zone_links else 1

            self.logger.info(f"[INFINITE_SCROLL] Found {len(additional_links)} additional links through infinite scroll")

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Error in strategy execution: {e}")

        return additional_links

    async def _exhaust_container_scroll(
        self,
        page: Page,
        container: Dict[str, Any],
        initial_content: Dict[str, int],
        loading_selectors: List[str],
        base_url: str,
        discovered_urls: Set[str],
        session_discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """Exhaust scrolling for a specific container."""
        additional_links = []
        max_scrolls = 10
        scroll_count = 0
        no_change_count = 0
        max_no_change = 3

        try:
            current_content = initial_content.copy()

            while scroll_count < max_scrolls and no_change_count < max_no_change:
                # Perform scroll action
                if container['element'] is None:
                    # Document scrolling
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                else:
                    # Container scrolling
                    await container['element'].evaluate("el => el.scrollTop = el.scrollHeight")

                # Wait for content to load using loading indicators
                await self._wait_for_content_load(page, loading_selectors)

                # Wait additional time for network requests
                await asyncio.sleep(self.delay * 2)

                # Check for new content using multiple metrics
                new_content = await self._get_content_metrics(page)
                content_changed = any(
                    new_content[key] > current_content[key]
                    for key in ['linkCount', 'productCount', 'cardCount', 'listItemCount']
                )

                if content_changed:
                    # Extract new links
                    html_content = await page.content()
                    new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                    # Filter for valid links not already discovered
                    valid_links = []
                    for link_info in new_links:
                        if (is_same_domain(link_info.url, self.domain)):
                            valid_links.append(link_info)
                            session_discovered_urls.add(link_info.url)  # Add to session tracker

                    additional_links.extend(valid_links)
                    current_content = new_content
                    no_change_count = 0

                    self.logger.info(f"[INFINITE_SCROLL] Found {len(valid_links)} new links, total: {len(additional_links)}")
                else:
                    no_change_count += 1
                    self.logger.debug(f"[INFINITE_SCROLL] No content change detected ({no_change_count}/{max_no_change})")

                scroll_count += 1

                # Check if we've reached the end
                if container['element'] is None:
                    # Check document scrolling
                    at_bottom = await page.evaluate('''
                        () => {
                            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                            const scrollHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
                            const clientHeight = window.innerHeight;
                            return scrollTop + clientHeight >= scrollHeight - 10;
                        }
                    ''')
                else:
                    # Check container scrolling
                    at_bottom = await container['element'].evaluate('''
                        el => el.scrollTop + el.clientHeight >= el.scrollHeight - 10
                    ''')

                if at_bottom and no_change_count > 0:
                    self.logger.info("[INFINITE_SCROLL] Reached bottom with no new content")
                    break

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Container scroll error: {e}")

        return additional_links

    async def _exhaust_trigger_zone(
        self,
        page: Page,
        trigger_zone: Dict[str, Any],
        initial_content: Dict[str, int],
        loading_selectors: List[str],
        base_url: str,
        discovered_urls: Set[str],
        session_discovered_urls: Set[str]
    ) -> List[LinkInfo]:
        """Exhaust infinite scroll by scrolling to trigger zones."""
        additional_links = []

        try:
            element = trigger_zone['element']

            # Scroll element into view
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(self.delay)

            # Wait for content to potentially load
            await self._wait_for_content_load(page, loading_selectors)
            await asyncio.sleep(self.delay * 2)

            # Check if content was added
            new_content = await self._get_content_metrics(page)
            content_changed = any(
                new_content[key] > initial_content[key]
                for key in ['linkCount', 'productCount', 'cardCount', 'listItemCount']
            )

            if content_changed:
                # Extract new links
                html_content = await page.content()
                new_links = extract_link_info_from_html(html_content, base_url, discovered_urls, len(additional_links), session_discovered_urls)

                # Filter for valid links
                for link_info in new_links:
                    if (is_same_domain(link_info.url, self.domain)):
                        additional_links.append(link_info)
                        session_discovered_urls.add(link_info.url)  # Add to session tracker

                self.logger.info(f"[INFINITE_SCROLL] Trigger zone activated, found {len(additional_links)} links")

        except Exception as e:
            self.logger.error(f"[INFINITE_SCROLL] Trigger zone error: {e}")

        return additional_links

    async def _wait_for_content_load(self, page: Page, loading_selectors: List[str]):
        """Wait for content to load using loading indicators."""
        if not loading_selectors:
            return

        try:
            # Wait for loading indicators to appear
            for selector in loading_selectors[:3]:  # Check first 3 selectors
                try:
                    await page.wait_for_selector(selector, timeout=1000, state='visible')
                    # Then wait for them to disappear or become hidden
                    await page.wait_for_selector(f'{selector}:not([style*="display: block"]):not(.visible)', timeout=5000)
                    break
                except Exception:
                    continue

        except Exception as e:
            self.logger.debug(f"[INFINITE_SCROLL] Loading indicator wait error: {e}")
            # Continue anyway as this is just an optimization