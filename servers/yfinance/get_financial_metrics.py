"""Auto-generated wrapper for yfinance → get_financial_metrics."""

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

TOOL = {'description': 'Get key financial metrics and ratios for fundamental analysis. Includes P/E ratio, profit margins, debt ratios, and growth rates.', 'inputSchema': {'properties': {'symbol': {'description': 'Stock ticker symbol', 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_financial_metrics'}

async def get_financial_metrics(*args: Any, **kwargs: Any) -> Any:
    """Get key financial metrics and ratios for fundamental analysis. Includes P/E ratio, profit margins, debt ratios, and growth rates."""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_financial_metrics')
