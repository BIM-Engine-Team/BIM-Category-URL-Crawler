Currently, i implemented a web crawler that tries to retreat all the links of a given website. The crawler use breadth-first search to explore the website and make a tree structure of the website's link.

Now I want to power the search with AI.Because we actually don't want get all the links, we just want all links that are the product description page.So I want to use ai to guide the exploration.

what we want for the output:
a json like this:

```
[
    {
        "productName": "Extreme Block Interior/Exterior Stain Blocking Waterbased Primer"
        "url": "https...."
    },
    {
        "productName": "Purdy Revolution 9" Frame"
        "url": "https...."
    },

]
```

How it's gonna work:

- The crawler will still host the tree as a map. But this time we don't use the breadth-first searching. We use ai to score nodes to decide which to explore next.

how do we process a node?

````pseudo
function ProcessNode(node):
    // Explore this node
    mark this node as Explored

    // Score Children
    children = get children links from the page of the node
    foreach children
        childrenInfo.add( get their title, description and relative path)

    instruction_prompt to ai (you can refine it for me) = """You come to a page with a list of links. Here is the relative path, title and description of each link.
    Score them from 0 - 10 according to how likely the link will lead you to the product description page.
    A score less than 1 is for links you will never click.
    A score higher than 9 is for links you think is very likely to be the product description page of a specific product. For these kind of link, you will also tell the product name.

    [Show the childrenInfo here]
    """

    output_structure_prompt = """Please format your response as JSON with the following structure:
    [
        {"score": 3.4},
        {"score": 7.8},
        {"score": 9.5, "productName": "Emerald Urethane Trim Enamel"} // provide product name when score is larger than 9
        ...
    ]"""

    get the answer from the ai and set the score of each children to their tree node.
    mark Explored to children less than 1 and larger than 9.
    add the rest of the children to the openSet
    add the productName, url for children higher than 9 to the final output
    return to explore the next node

```

The openSet

- implement it as a max binary heap
- the element's value for sorting is the average score of the node and all its ancestors. For example, for node3 : root - node1 - node2 - node3, its value for sorting in the open set is (score1 + score2 + score3)/3

how do we decide which node to explore next?
    - The element with max value in the open set;

NOTES:
1. We use this system prompt for all request to ai for this plan (you can refine it for me):
    "You are an architect. You want to find the product information from a supplier's website. You are clicking the button to go to the production description page."
2.
````
