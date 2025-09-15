from typing import List, Dict, Any


class PromptTemplates:

    @staticmethod
    def exploration_decision(page_url: str, page_content: str, current_depth: int,
                           visited_count: int, context: Dict[str, Any]) -> str:
        return f"""
You are analyzing a webpage to decide exploration strategy for a website crawler focused on architecture materials.

Page URL: {page_url}
Current Depth: {current_depth}
Pages Visited: {visited_count}
Context: {context}

Page Content Summary:
{page_content[:2000]}...

Task: Analyze this page and provide exploration decisions:

1. PRIORITY LINKS: Which links should be explored next? Focus on architecture materials (doors, windows, roofing, flooring, etc.)
2. LEAF NODE: Is this a terminal page that doesn't need further exploration?
3. PAGE TYPE: Classify this page (homepage, category, product, listing, other)
4. RELEVANCE: Rate content relevance for architecture materials (1-10)

Respond in JSON format:
{{
    "priority_links": ["url1", "url2", ...],
    "is_leaf_node": boolean,
    "page_type": "category|product|listing|homepage|other",
    "relevance_score": integer,
    "reasoning": "brief explanation"
}}
"""

    @staticmethod
    def series_detection(links: List[str], base_url: str) -> str:
        links_text = "\n".join(links[:50])  # Limit for token efficiency

        return f"""
You are analyzing links from a website to detect patterns and series.

Base URL: {base_url}
Links to analyze:
{links_text}

Task: Identify link series/patterns such as:
- Pagination: /products?page=1, /products?page=2, etc.
- Categories: /category/doors, /category/windows, etc.
- Product variants: /product/123, /product/456, etc.

For each detected series:
1. Group similar links by pattern
2. Select 3-5 representative samples
3. Estimate total count in series
4. Classify series type

Respond in JSON format:
{{
    "detected_series": [
        {{
            "pattern_id": "unique_id",
            "url_pattern": "/products?page={{num}}",
            "sample_urls": ["url1", "url2", "url3"],
            "total_count": estimated_number,
            "series_type": "pagination|category|product_variant"
        }}
    ],
    "individual_links": ["links_not_part_of_series"],
    "reasoning": "brief explanation of patterns found"
}}
"""

    @staticmethod
    def link_relevance(links: List[str], page_context: str) -> str:
        links_text = "\n".join(links[:30])

        return f"""
You are filtering links for relevance to architecture materials and building supplies.

Page Context: {page_context}

Links to evaluate:
{links_text}

Task: Filter links based on relevance to architecture materials:
- HIGH: Product catalogs, material categories, specifications
- MEDIUM: Related categories, technical resources
- LOW: Contact pages, legal, user accounts

Focus on: doors, windows, roofing, flooring, siding, tiles, lumber, hardware, fixtures, construction materials

Respond in JSON format:
{{
    "high_priority": ["most_relevant_urls"],
    "medium_priority": ["moderately_relevant_urls"],
    "low_priority": ["less_relevant_urls"],
    "skip": ["irrelevant_urls"],
    "reasoning": "brief explanation"
}}
"""

    @staticmethod
    def content_classification(url: str, content: str, title: str) -> str:
        return f"""
You are classifying webpage content for a crawler focused on architecture materials.

URL: {url}
Title: {title}
Content: {content[:1500]}...

Task: Classify this page and extract key information:

1. PAGE TYPE: What type of page is this?
2. CONTENT RELEVANCE: How relevant is this to architecture materials?
3. KEY METADATA: Extract important information for crawling schema

Respond in JSON format:
{{
    "page_type": "homepage|category|product|listing|navigation|other",
    "relevance_score": integer_1_to_10,
    "is_architecture_related": boolean,
    "key_metadata": {{
        "has_products": boolean,
        "has_categories": boolean,
        "has_specifications": boolean,
        "navigation_depth": integer
    }},
    "extracted_info": {{
        "product_count": integer_or_null,
        "category_names": ["list_of_categories"],
        "key_features": ["list_of_important_features"]
    }},
    "reasoning": "brief explanation"
}}
"""