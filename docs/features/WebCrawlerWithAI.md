Currently, i implemented a web crawler that tries to retreat all the links of a given website. The crawler use breadth-first search to explore the website and make a tree structure of the website's link.

Now I want to power the search with AI.Because we actually don't want get all the links, we just want all links that are the product description page.So I want to use ai to guide the exploration.

what we want for the output:
a json like this:

```
[
    {
        "production name": "Extreme Block Interior/Exterior Stain Blocking Waterbased Primer"
        "url": "https...."
    },
    {
        "production name": "Purdy Revolution 9" Frame"
        "url": "https...."
    },

]
```

How it's gonna work:

- The crawler will still host the tree as a map. But this time we don't use the breadth-first searching. We use ai to score nodes to decide which to explore next.

node state:

- Unexplored,
  - default
- Explored,
  - for nodes which have be processed with the ProcessNode() method but not marked as CompletelyExplored
- CompletelyExplored
  - for nodes that were scored less than 1 or are the project description page
  - for nodes don't have children
  - for nodes all children of whom are marked CompletelyExplored
  - check and update the parent node's state whenever there is a node marked as CompletelyExplored

how do we decide which node to explore next?

- we compare all nodes that are not Unexplored and take the one with highest score (regardless of its depth).

how do we process a node?

```pseudo
function ProcessNode(node):
    // Explore this node
    visit the page
    nodeInfo = its title, description and relative path (relative to its direct parent)
    ask ai:
        instruction_prompt (you can refine it for me) = '''According to the following information.Do you think this page is a description page of a specific product? If yes, answer with ONLY the production name; if no, answer exactly "No".
        [Show the nodeInfo]
        '''

    if yes, add this to the final output, increase the score of its brother nodes by 10%. mark this node as CompletelyExplored. return. explore the next node
    if no, score its children.

    // Score Children
    children = get children links from the node
    foreach children
    get their title

    childrenInfo = [child1's relative path (relative to its direct parent) & its title, child2's relative path & its title, ...]


    instruction_prompt to ai (you can refine it for me) = """This is a list of link's path and title on the current page.
    Score them from 0 - 10 according to how likely it will lead you to the product description page. a score less than 1 is for links you will never click.

    [Show the childrenInfo here]
    """

    output_structure_prompt = """Please format your response as JSON with the following structure:
    [
        {"score": 3.4},
        {"score": 7.8},
        ...
    ]"""

    get the answer from the ai and set the score of each children. mark CompletelyExplored to children less than 1.
    mark this node as Explored.
    explore the next node

```

We use this system prompt for all request to ai for this plan (you can refine it for me):
"You are an architect. You want to find the product information from a supplier's website. You are clicking the button to go to the production description page."
