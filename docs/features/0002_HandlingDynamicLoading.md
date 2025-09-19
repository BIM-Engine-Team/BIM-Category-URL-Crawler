Currently, i implemented a web crawler to scrape all product description url. The crawler searches for target pages effectively based on a scoring system using AI.
But the crawler is not capable of handling pages using dynamic loading yet.
I would like to implement this feature as follow:

1. We might meet the following kind of dynamic loading. each kind has their specific way to check or to exhaust.

   - Pagination
   - Load More
   - Infinite Scroll
   - Tabs
   - Accordions
   - Expanders

2. which kind of node should we check if there are any dynamic loading?

   - in the "process_node" function of "ai_crawler.py", when we found one or more children that are production description pages, we need to check if this node uses dynamic load
   - this happens right after you finished handling scoring results in the "process_node" function of "ai_crawler.py"

3. How to check if this is a page with dynamic loading?

   - we ask ai:
     - instruction prompt = "On this page, you found multiple links to product description pages. According to the UI elements on this page, do you think the page uses dynamic loading? If yes, output the element's id and tell its trigger type (select one from: Pagination, Load More, Tabs, Accordions, Expanders), if no, you answer with '{"id" = -1}'. Here is the list of elements: [list of children info(see instruction below)]"
     - list of children info: you copy the children_info from the one created in process_node(), prune unused fields, only keep relative link, link_tag, link_text, id.
     - output structure prompt = '{"id" = 3, "triggerType" = "Pagination"}'
     - then you find the responding information using this id and
   - if the answer is yes, we should check all elements in the answer
   - whether the answer is yes or not, we need to check if the page has a Infinite Scroll
   - we will use playwright to click or scroll to see if there is any change that we are interested in for checking

4. When we detect a dynamic load feature, we should use playwright to exhaust all possible options of the feature and record all links we get.
   - for new links we got, we still need to check if it's within our search scope, whether it's duplicated, whether it's valid, just like we did in the create_link_info()

NOTES:

1. We use this system prompt for all request to ai for this plan (you can refine it for me):
   "You are an architect. You want to find the product information from a supplier's website. You are clicking the button to go to the production description page."

---

## PATCH: Playwright Wait Strategy Optimization (2025-09-18)

**Issue:** Original implementation used `wait_until="networkidle"` causing timeouts on analytics-heavy sites.

**Root Cause:** Modern e-commerce sites have continuous network activity (analytics, tracking, A/B testing) that prevents networkidle condition from ever being met.

**Solution Applied:**

1. **Initial Page Load:** Changed `networkidle` → `domcontentloaded` for faster, reliable loading
2. **Trigger-Specific Waits:** Replaced generic network waiting with targeted `page.wait_for_selector()` strategies:
   - **Pagination:** Wait for `.pagination-content`, `.product-list`, monitor link count changes
   - **Load More:** Wait for `.loaded-content`, `.new-items`, track loading indicators
   - **Tabs:** Wait for `.tab-content.active`, `[aria-hidden="false"]`, verify visibility
   - **Accordions/Expanders:** Wait for `[aria-expanded="true"]`, `.expanded`, monitor height changes

3. **Enhanced Error Handling:** Added robust JSON parsing with detailed error logging for AI responses

**Result:** Eliminates timeout errors, faster execution, more reliable dynamic content detection.
