we want to collect information about architecture material product from supplier's website.
Because each supplier's website varies on the structure. I want to make a ai agent to do the job.

1. EXPLORE PART: The ai will firstly explore the whole website and construct a structure tree according to which we can construct a crawling schema later.
2. SCHEMA PART: Then the ai will construct a crawling schema from the tree.
3. EXECUTE PART: The code will use this schema to call the utilities to crawl the product information (This part may not involve AI)

EXPLORE PART

1. the agent starts from the home page
2. the agent use tools to get a clean and concise structure of the page
3. it extract the possible links in the page structure into tree nodes to guide the exploration and to record the link that has been explore.
   1. about tree structure: in a web page, there may be a series of similar links. For example, a series of wooded tiles. We know that we get the similar result when we click any of them. So the ai agent should recognize this and the tree structure should be capable of handling this so that we don't need to explore each of the link.
4. it analyze the page structure to see if this is the "leaf" of the website.
   1. If is the "leaf", see if there is any product information
      1. if yes, this is a valid path
      2. if no, this is a invalid path
   2. If not the "leaf", check the tree and see which node is more likely to go to a valid leaf
5. repeat 2-4 until all potential nodes are explored
