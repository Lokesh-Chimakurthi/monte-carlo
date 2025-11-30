"""Auto-generated TypedDict interfaces for tavily MCP tools.

These interfaces provide type hints for tool parameters.
Import and use these for IDE autocompletion and type checking.
"""

from __future__ import annotations

from typing import Any, List, Optional, TypedDict, Literal

# Search the web for real-time information about any topic. Use this tool when you need up-to-date information that might not be available in your training data, or when you need to verify current facts. The search results will include relevant snippets and URLs from web pages. This is particularly useful for questions about current events, technology updates, or any topic that requires recent information.
class TavilyTavilySearchInput(TypedDict):
    # Search query
    query: str
    # The maximum number of search results to return
    max_results: Optional[int]
    # The depth of the search. It can be 'basic' or 'advanced'
    search_depth: Optional[Literal["basic", "advanced"]]
    # The category of the search. This will determine which of our agents will be used
    topic: Optional[Literal["general", "news", "finance"]]
    # The number of days back from the current date to include in the search results. 
    days: Optional[int]
    # The time range back from the current date to include in the search results. This
    time_range: Optional[Literal["day", "week", "month", "year", "d", "w", "m", "y"]]
    # Include a list of query-related images in the response
    include_images: Optional[bool]
    # Include a list of query-related images and their descriptions in the response
    include_image_descriptions: Optional[bool]
    # Include the cleaned and parsed HTML content of each search result
    include_raw_content: Optional[bool]
    # A list of domains to specifically include in the search results, if the user ask
    include_domains: Optional[List[str]]
    # List of domains to specifically exclude, if the user asks to exclude a domain se
    exclude_domains: Optional[List[str]]
    # Boost search results from a specific country. This will prioritize content from 
    country: Optional[str]
    # Whether to include the favicon URL for each result
    include_favicon: Optional[bool]
    # Will return all results after the specified start date ( publish date ). Require
    start_date: Optional[str]
    # Will return all results before the specified end date ( publish date ). Required
    end_date: Optional[str]

# Extract and process content from specific web pages. Use this tool when you have URLs and need to get the full text content from those pages. Returns clean, structured content in markdown or text format. Useful for reading articles, documentation, or any web page content that you need to analyze or reference.
class TavilyTavilyExtractInput(TypedDict):
    # List of URLs to extract content from
    urls: List[str]
    # Depth of extraction - 'basic' or 'advanced', if usrls are linkedin use 'advanced
    extract_depth: Optional[Literal["basic", "advanced"]]
    # Include a list of images extracted from the urls in the response
    include_images: Optional[bool]
    # The format of the extracted web page content. markdown returns content in markdo
    format: Optional[Literal["markdown", "text"]]
    # Whether to include the favicon URL for each result
    include_favicon: Optional[bool]

# Crawl multiple pages from a website starting from a base URL. Use this tool when you need to gather information from multiple related pages across a website or explore a site's structure. It follows internal links and extracts content from multiple pages, but truncates content to 500 characters per page. For full content extraction, use tavily_map to discover URLs first, then tavily_extract to get complete content from specific pages. Useful for comprehensive research on documentation sites, blogs, or when you need to understand the full scope of information available on a website.
class TavilyTavilyCrawlInput(TypedDict):
    # The root URL to begin the crawl
    url: str
    # Max depth of the crawl. Defines how far from the base URL the crawler can explor
    max_depth: Optional[int]
    # Max number of links to follow per level of the graph (i.e., per page)
    max_breadth: Optional[int]
    # Total number of links the crawler will process before stopping
    limit: Optional[int]
    # Natural language instructions for the crawler. Instructions specify which types 
    instructions: Optional[str]
    # Regex patterns to select only URLs with specific path patterns (e.g., /docs/.*, 
    select_paths: Optional[List[str]]
    # Regex patterns to restrict crawling to specific domains or subdomains (e.g., ^do
    select_domains: Optional[List[str]]
    # Regex patterns to exclude URLs from the crawl with specific path patterns
    exclude_paths: Optional[List[str]]
    # Regex patterns to exclude URLs from specific domains or subdomains
    exclude_domains: Optional[List[str]]
    # Whether to return external links in the final response
    allow_external: Optional[bool]
    # Whether to include images in the crawl results
    include_images: Optional[bool]
    # Advanced extraction retrieves more data, including tables and embedded content, 
    extract_depth: Optional[Literal["basic", "advanced"]]
    # The format of the extracted web page content. markdown returns content in markdo
    format: Optional[Literal["markdown", "text"]]
    # Whether to include the favicon URL for each result
    include_favicon: Optional[bool]

# Map and discover the structure of a website by finding all its URLs and pages. Use this tool when you need to understand a website's organization, find specific pages, or get an overview of all available content without extracting the actual text. Returns a structured list of URLs and their relationships. Useful for site exploration, finding documentation pages, or understanding how a website is organized.
class TavilyTavilyMapInput(TypedDict):
    # The root URL to begin the mapping
    url: str
    # Max depth of the mapping. Defines how far from the base URL the crawler can expl
    max_depth: Optional[int]
    # Max number of links to follow per level of the graph (i.e., per page)
    max_breadth: Optional[int]
    # Total number of links the crawler will process before stopping
    limit: Optional[int]
    # Natural language instructions for the crawler
    instructions: Optional[str]
    # Regex patterns to select only URLs with specific path patterns (e.g., /docs/.*, 
    select_paths: Optional[List[str]]
    # Regex patterns to restrict crawling to specific domains or subdomains (e.g., ^do
    select_domains: Optional[List[str]]
    # Regex patterns to exclude URLs from the crawl with specific path patterns
    exclude_paths: Optional[List[str]]
    # Regex patterns to exclude URLs from specific domains or subdomains
    exclude_domains: Optional[List[str]]
    # Whether to return external links in the final response
    allow_external: Optional[bool]

__all__ = ("TavilyTavilySearchInput", "TavilyTavilyExtractInput", "TavilyTavilyCrawlInput", "TavilyTavilyMapInput",)
