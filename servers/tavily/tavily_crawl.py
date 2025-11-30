"""Auto-generated wrapper for tavily-mcp → tavily_crawl."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from servers._runtime import call_tool
except ImportError:  # Modal uploads omit the 'servers' package
    import sys
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.append(root_str)
    from _runtime import call_tool

TOOL = {'_meta': {'_fastmcp': {'tags': []}}, 'description': "Crawl multiple pages from a website starting from a base URL. Use this tool when you need to gather information from multiple related pages across a website or explore a site's structure. It follows internal links and extracts content from multiple pages, but truncates content to 500 characters per page. For full content extraction, use tavily_map to discover URLs first, then tavily_extract to get complete content from specific pages. Useful for comprehensive research on documentation sites, blogs, or when you need to understand the full scope of information available on a website.", 'inputSchema': {'properties': {'allow_external': {'default': True, 'description': 'Whether to return external links in the final response', 'type': 'boolean'}, 'exclude_domains': {'default': [], 'description': 'Regex patterns to exclude URLs from specific domains or subdomains', 'items': {'type': 'string'}, 'type': 'array'}, 'exclude_paths': {'default': [], 'description': 'Regex patterns to exclude URLs from the crawl with specific path patterns', 'items': {'type': 'string'}, 'type': 'array'}, 'extract_depth': {'default': 'basic', 'description': 'Advanced extraction retrieves more data, including tables and embedded content, with higher success but may increase latency', 'enum': ['basic', 'advanced'], 'type': 'string'}, 'format': {'default': 'markdown', 'description': 'The format of the extracted web page content. markdown returns content in markdown format. text returns plain text and may increase latency.', 'enum': ['markdown', 'text'], 'type': 'string'}, 'include_favicon': {'default': False, 'description': 'Whether to include the favicon URL for each result', 'type': 'boolean'}, 'include_images': {'default': False, 'description': 'Whether to include images in the crawl results', 'type': 'boolean'}, 'instructions': {'default': '', 'description': 'Natural language instructions for the crawler. Instructions specify which types of pages the crawler should return.', 'type': 'string'}, 'limit': {'default': 50, 'description': 'Total number of links the crawler will process before stopping', 'minimum': 1, 'type': 'integer'}, 'max_breadth': {'default': 20, 'description': 'Max number of links to follow per level of the graph (i.e., per page)', 'minimum': 1, 'type': 'integer'}, 'max_depth': {'default': 1, 'description': 'Max depth of the crawl. Defines how far from the base URL the crawler can explore.', 'minimum': 1, 'type': 'integer'}, 'select_domains': {'default': [], 'description': 'Regex patterns to restrict crawling to specific domains or subdomains (e.g., ^docs\\.example\\.com$)', 'items': {'type': 'string'}, 'type': 'array'}, 'select_paths': {'default': [], 'description': 'Regex patterns to select only URLs with specific path patterns (e.g., /docs/.*, /api/v1.*)', 'items': {'type': 'string'}, 'type': 'array'}, 'url': {'description': 'The root URL to begin the crawl', 'type': 'string'}}, 'required': ['url'], 'type': 'object'}, 'name': 'tavily_crawl', 'outputSchema': {'additionalProperties': True, 'type': 'object'}}

async def tavily_crawl(*args: Any, **kwargs: Any) -> Any:
    """Crawl multiple pages from a website starting from a base URL. Use this tool when you need to gather information from multiple related pages across a website or explore a site's structure. It follows internal links and extracts content from multiple pages, but truncates content to 500 characters per page. For full content extraction, use tavily_map to discover URLs first, then tavily_extract to get complete content from specific pages. Useful for comprehensive research on documentation sites, blogs, or when you need to understand the full scope of information available on a website."""
    return await call_tool("tavily", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'tavily_crawl')
