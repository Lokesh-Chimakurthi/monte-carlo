"""Auto-generated wrapper for tavily-mcp → tavily_search."""

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

TOOL = {'_meta': {'_fastmcp': {'tags': []}}, 'description': 'Search the web for real-time information about any topic. Use this tool when you need up-to-date information that might not be available in your training data, or when you need to verify current facts. The search results will include relevant snippets and URLs from web pages. This is particularly useful for questions about current events, technology updates, or any topic that requires recent information.', 'inputSchema': {'properties': {'country': {'default': '', 'description': 'Boost search results from a specific country. This will prioritize content from the selected country in the search results. Available only if topic is general.', 'type': 'string'}, 'days': {'default': 30, 'description': "The number of days back from the current date to include in the search results. This specifies the time frame of data to be retrieved. Please note that this feature is only available when using the 'news' search topic", 'type': 'integer'}, 'end_date': {'default': '', 'description': 'Will return all results before the specified end date ( publish date ). Required to be written in the format YYYY-MM-DD', 'type': 'string'}, 'exclude_domains': {'default': [], 'description': 'List of domains to specifically exclude, if the user asks to exclude a domain set this to the domain of the site', 'items': {'type': 'string'}, 'type': 'array'}, 'include_domains': {'default': [], 'description': 'A list of domains to specifically include in the search results, if the user asks to search on specific sites set this to the domain of the site', 'items': {'type': 'string'}, 'type': 'array'}, 'include_favicon': {'default': False, 'description': 'Whether to include the favicon URL for each result', 'type': 'boolean'}, 'include_image_descriptions': {'default': False, 'description': 'Include a list of query-related images and their descriptions in the response', 'type': 'boolean'}, 'include_images': {'default': False, 'description': 'Include a list of query-related images in the response', 'type': 'boolean'}, 'include_raw_content': {'default': False, 'description': 'Include the cleaned and parsed HTML content of each search result', 'type': 'boolean'}, 'max_results': {'default': 5, 'description': 'The maximum number of search results to return', 'type': 'integer'}, 'query': {'description': 'Search query', 'type': 'string'}, 'search_depth': {'default': 'basic', 'description': "The depth of the search. It can be 'basic' or 'advanced'", 'enum': ['basic', 'advanced'], 'type': 'string'}, 'start_date': {'default': '', 'description': 'Will return all results after the specified start date ( publish date ). Required to be written in the format YYYY-MM-DD', 'type': 'string'}, 'time_range': {'default': 'month', 'description': "The time range back from the current date to include in the search results. This feature is available for both 'general' and 'news' search topics", 'enum': ['day', 'week', 'month', 'year', 'd', 'w', 'm', 'y'], 'type': 'string'}, 'topic': {'default': 'general', 'description': 'The category of the search. This will determine which of our agents will be used for the search', 'enum': ['general', 'news', 'finance'], 'type': 'string'}}, 'required': ['query'], 'type': 'object'}, 'name': 'tavily_search', 'outputSchema': {'additionalProperties': True, 'type': 'object'}}

async def tavily_search(*args: Any, **kwargs: Any) -> Any:
    """Search the web for real-time information about any topic. Use this tool when you need up-to-date information that might not be available in your training data, or when you need to verify current facts. The search results will include relevant snippets and URLs from web pages. This is particularly useful for questions about current events, technology updates, or any topic that requires recent information."""
    return await call_tool("tavily", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'tavily_search')
