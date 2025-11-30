"""Auto-generated wrapper for tavily-mcp → tavily_extract."""

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

TOOL = {'_meta': {'_fastmcp': {'tags': []}}, 'description': 'Extract and process content from specific web pages. Use this tool when you have URLs and need to get the full text content from those pages. Returns clean, structured content in markdown or text format. Useful for reading articles, documentation, or any web page content that you need to analyze or reference.', 'inputSchema': {'properties': {'extract_depth': {'default': 'basic', 'description': "Depth of extraction - 'basic' or 'advanced', if usrls are linkedin use 'advanced' or if explicitly told to use advanced", 'enum': ['basic', 'advanced'], 'type': 'string'}, 'format': {'default': 'markdown', 'description': 'The format of the extracted web page content. markdown returns content in markdown format. text returns plain text and may increase latency.', 'enum': ['markdown', 'text'], 'type': 'string'}, 'include_favicon': {'default': False, 'description': 'Whether to include the favicon URL for each result', 'type': 'boolean'}, 'include_images': {'default': False, 'description': 'Include a list of images extracted from the urls in the response', 'type': 'boolean'}, 'urls': {'description': 'List of URLs to extract content from', 'items': {'type': 'string'}, 'type': 'array'}}, 'required': ['urls'], 'type': 'object'}, 'name': 'tavily_extract', 'outputSchema': {'additionalProperties': True, 'type': 'object'}}

async def tavily_extract(*args: Any, **kwargs: Any) -> Any:
    """Extract and process content from specific web pages. Use this tool when you have URLs and need to get the full text content from those pages. Returns clean, structured content in markdown or text format. Useful for reading articles, documentation, or any web page content that you need to analyze or reference."""
    return await call_tool("tavily", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'tavily_extract')
