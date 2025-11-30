"""Auto-generated tool package for yfinance.

Usage:
    from servers.yfinance import <tool_function>

Example:
    from servers.yfinance import get_stock_quote
    result = await get_stock_quote(param=value)
"""

from __future__ import annotations

from . import get_stock_quote as _get_stock_quote_module
from . import get_stock_history as _get_stock_history_module
from . import get_company_info as _get_company_info_module
from . import get_financial_metrics as _get_financial_metrics_module
from . import calculate_volatility as _calculate_volatility_module
from . import get_market_index as _get_market_index_module
from . import compare_stocks as _compare_stocks_module

# Re-export tool functions for convenient imports
from .get_stock_quote import get_stock_quote
from .get_stock_history import get_stock_history
from .get_company_info import get_company_info
from .get_financial_metrics import get_financial_metrics
from .calculate_volatility import calculate_volatility
from .get_market_index import get_market_index
from .compare_stocks import compare_stocks
from . import manifest

# Non-sensitive defaults for this provider.
SERVER_CONFIG = {'args': ['run', 'python', '_mcp_servers/yfinance_server.py'], 'command': 'uv', 'cwd': None, 'read_timeout': 30.0, 'timeout': 30.0, 'transport': 'stdio'}

__all__ = ("get_stock_quote", "get_stock_history", "get_company_info", "get_financial_metrics", "calculate_volatility", "get_market_index", "compare_stocks", "manifest", "SERVER_CONFIG",)
