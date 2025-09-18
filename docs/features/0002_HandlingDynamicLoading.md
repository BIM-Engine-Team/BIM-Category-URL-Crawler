Currently, i implemented a web crawler to scrape all product description url. The crawler searches for target pages effectively based on a scoring system using AI.
But the crawler is not capable of handling pages using dynamic loading yet.
I would like to implement this feature as follow:

1. what kind of dynamic loading are there?

   - Pagination
   - Load More
   - Infinite Scroll
   - Tabs
   - Accordions / Expanders

2. which kind of node should we check if there are any dynamic loading?

   - in the "process_node" function of "ai_crawler.py", when we found one or more children that are production description pages, we need to check if this node uses dynamic load

3. How to check if this is a page with dynamic loading?
   - this happens right after ai scores children in the "process_node" function of "ai_crawler.py" when the we get one or more score higher than 9
   - pass the children_info which only contain relative link, link tag and
   -
