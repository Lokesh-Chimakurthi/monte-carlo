"""Auto-generated wrapper for yfinance → get_stock_quote."""

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

TOOL = {'description': 'Get current stock quote with price, volume, and basic metrics. Returns real-time market data for a given stock symbol.', 'inputSchema': {'properties': {'symbol': {'description': "Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'SBUX')", 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_stock_quote'}

async def get_stock_quote(*args: Any, **kwargs: Any) -> Any:
    """Get current stock quote with price, volume, and basic metrics. Returns real-time market data for a given stock symbol."""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_stock_quote')
