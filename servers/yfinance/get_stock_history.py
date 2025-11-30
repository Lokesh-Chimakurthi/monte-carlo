"""Auto-generated wrapper for yfinance → get_stock_history."""

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

TOOL = {'description': 'Get historical stock price data for a given period. Useful for analyzing trends and volatility for Monte Carlo simulations.', 'inputSchema': {'properties': {'interval': {'default': '1d', 'description': 'Data interval', 'enum': ['1d', '1wk', '1mo'], 'type': 'string'}, 'period': {'default': '1y', 'description': 'Time period for historical data', 'enum': ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'], 'type': 'string'}, 'symbol': {'description': "Stock ticker symbol (e.g., 'AAPL', 'GOOGL')", 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_stock_history'}

async def get_stock_history(*args: Any, **kwargs: Any) -> Any:
    """Get historical stock price data for a given period. Useful for analyzing trends and volatility for Monte Carlo simulations."""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_stock_history')
