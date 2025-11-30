"""Auto-generated wrapper for yfinance → calculate_volatility."""

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

TOOL = {'description': 'Calculate historical volatility (standard deviation of returns) for risk assessment in simulations.', 'inputSchema': {'properties': {'period': {'default': '1y', 'description': 'Period for volatility calculation', 'enum': ['1mo', '3mo', '6mo', '1y', '2y'], 'type': 'string'}, 'symbol': {'description': 'Stock ticker symbol', 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'calculate_volatility'}

async def calculate_volatility(*args: Any, **kwargs: Any) -> Any:
    """Calculate historical volatility (standard deviation of returns) for risk assessment in simulations."""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'calculate_volatility')
