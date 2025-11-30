"""Auto-generated wrapper for tavily-mcp → tavily_map."""

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

TOOL = {'_meta': {'_fastmcp': {'tags': []}}, 'description': "Map and discover the structure of a website by finding all its URLs and pages. Use this tool when you need to understand a website's organization, find specific pages, or get an overview of all available content without extracting the actual text. Returns a structured list of URLs and their relationships. Useful for site exploration, finding documentation pages, or understanding how a website is organized.", 'inputSchema': {'properties': {'allow_external': {'default': True, 'description': 'Whether to return external links in the final response', 'type': 'boolean'}, 'exclude_domains': {'default': [], 'description': 'Regex patterns to exclude URLs from specific domains or subdomains', 'items': {'type': 'string'}, 'type': 'array'}, 'exclude_paths': {'default': [], 'description': 'Regex patterns to exclude URLs from the crawl with specific path patterns', 'items': {'type': 'string'}, 'type': 'array'}, 'instructions': {'default': '', 'description': 'Natural language instructions for the crawler', 'type': 'string'}, 'limit': {'default': 50, 'description': 'Total number of links the crawler will process before stopping', 'minimum': 1, 'type': 'integer'}, 'max_breadth': {'default': 20, 'description': 'Max number of links to follow per level of the graph (i.e., per page)', 'minimum': 1, 'type': 'integer'}, 'max_depth': {'default': 1, 'description': 'Max depth of the mapping. Defines how far from the base URL the crawler can explore', 'minimum': 1, 'type': 'integer'}, 'select_domains': {'default': [], 'description': 'Regex patterns to restrict crawling to specific domains or subdomains (e.g., ^docs\\.example\\.com$)', 'items': {'type': 'string'}, 'type': 'array'}, 'select_paths': {'default': [], 'description': 'Regex patterns to select only URLs with specific path patterns (e.g., /docs/.*, /api/v1.*)', 'items': {'type': 'string'}, 'type': 'array'}, 'url': {'description': 'The root URL to begin the mapping', 'type': 'string'}}, 'required': ['url'], 'type': 'object'}, 'name': 'tavily_map', 'outputSchema': {'additionalProperties': True, 'type': 'object'}}

async def tavily_map(*args: Any, **kwargs: Any) -> Any:
    """Map and discover the structure of a website by finding all its URLs and pages. Use this tool when you need to understand a website's organization, find specific pages, or get an overview of all available content without extracting the actual text. Returns a structured list of URLs and their relationships. Useful for site exploration, finding documentation pages, or understanding how a website is organized."""
    return await call_tool("tavily", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'tavily_map')
