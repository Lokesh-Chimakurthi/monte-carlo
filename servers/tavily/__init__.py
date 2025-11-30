"""Auto-generated tool package for tavily-mcp.

Usage:
    from servers.tavily import <tool_function>

Example:
    from servers.tavily import tavily_search
    result = await tavily_search(param=value)
"""

from __future__ import annotations

import os

from . import manifest
from . import tavily_crawl as _tavily_crawl_module
from . import tavily_extract as _tavily_extract_module
from . import tavily_map as _tavily_map_module
from . import tavily_search as _tavily_search_module
from .tavily_crawl import tavily_crawl
from .tavily_extract import tavily_extract
from .tavily_map import tavily_map

# Re-export tool functions for convenient imports
from .tavily_search import tavily_search

tavily_api = os.getenv("TAVILY_API_KEY")
# Non-sensitive defaults for this provider.
SERVER_CONFIG = {
    "read_timeout": 300.0,
    "timeout": 30.0,
    "transport": "http",
    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api}",
}

__all__ = (
    "tavily_search",
    "tavily_extract",
    "tavily_crawl",
    "tavily_map",
    "manifest",
    "SERVER_CONFIG",
)
