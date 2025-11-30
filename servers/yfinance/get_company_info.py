"""Auto-generated wrapper for yfinance → get_company_info."""

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

TOOL = {'description': 'Get detailed company information including sector, industry, market cap, and financial ratios. Essential for business analysis.', 'inputSchema': {'properties': {'symbol': {'description': 'Stock ticker symbol', 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_company_info'}

async def get_company_info(*args: Any, **kwargs: Any) -> Any:
    """Get detailed company information including sector, industry, market cap, and financial ratios. Essential for business analysis."""
    return await call_tool("yfinance", TOOL, *args, **kwargs)

__all__ = ('TOOL', 'get_company_info')
