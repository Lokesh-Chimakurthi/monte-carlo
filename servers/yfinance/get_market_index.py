"""Auto-generated wrapper for yfinance → get_market_index."""

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

TOOL = {'description': 'Get current data for major market indices (S&P 500, NASDAQ, Dow Jones, etc.)', 'inputSchema': {'properties': {'index': {'default': '^GSPC', 'description': 'Market index to fetch', 'enum': ['^GSPC', '^IXIC', '^DJI', '^RUT', '^VIX'], 'type': 'string'}}, 'required': [], 'type': 'object'}, 'name': 'get_market_index'}

async def get_market_index(*args: Any, **kwargs: Any) -> Any:
    """Get current data for major market indices (S&P 500, NASDAQ, Dow Jones, etc.)"""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_market_index')
