"""Tool manifest for yfinance.

Provides lightweight search + schema lookup so sandboxes can discover tools without
loading every wrapper module.
"""

from __future__ import annotations

from typing import Any, List

TOOLS: List[dict[str, Any]] = [{'description': 'Get current stock quote with price, volume, and basic metrics. Returns real-time market data for a given stock symbol.', 'inputSchema': {'properties': {'symbol': {'description': "Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'SBUX')", 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_stock_quote'}, {'description': 'Get historical stock price data for a given period. Useful for analyzing trends and volatility for Monte Carlo simulations.', 'inputSchema': {'properties': {'interval': {'default': '1d', 'description': 'Data interval', 'enum': ['1d', '1wk', '1mo'], 'type': 'string'}, 'period': {'default': '1y', 'description': 'Time period for historical data', 'enum': ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'], 'type': 'string'}, 'symbol': {'description': "Stock ticker symbol (e.g., 'AAPL', 'GOOGL')", 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_stock_history'}, {'description': 'Get detailed company information including sector, industry, market cap, and financial ratios. Essential for business analysis.', 'inputSchema': {'properties': {'symbol': {'description': 'Stock ticker symbol', 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_company_info'}, {'description': 'Get key financial metrics and ratios for fundamental analysis. Includes P/E ratio, profit margins, debt ratios, and growth rates.', 'inputSchema': {'properties': {'symbol': {'description': 'Stock ticker symbol', 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'get_financial_metrics'}, {'description': 'Calculate historical volatility (standard deviation of returns) for risk assessment in simulations.', 'inputSchema': {'properties': {'period': {'default': '1y', 'description': 'Period for volatility calculation', 'enum': ['1mo', '3mo', '6mo', '1y', '2y'], 'type': 'string'}, 'symbol': {'description': 'Stock ticker symbol', 'type': 'string'}}, 'required': ['symbol'], 'type': 'object'}, 'name': 'calculate_volatility'}, {'description': 'Get current data for major market indices (S&P 500, NASDAQ, Dow Jones, etc.)', 'inputSchema': {'properties': {'index': {'default': '^GSPC', 'description': 'Market index to fetch', 'enum': ['^GSPC', '^IXIC', '^DJI', '^RUT', '^VIX'], 'type': 'string'}}, 'required': [], 'type': 'object'}, 'name': 'get_market_index'}, {'description': 'Compare key metrics across multiple stocks for competitive analysis.', 'inputSchema': {'properties': {'symbols': {'description': 'List of stock ticker symbols to compare (max 5)', 'items': {'type': 'string'}, 'type': 'array'}}, 'required': ['symbols'], 'type': 'object'}, 'name': 'compare_stocks'}]


def search_tools(query: str) -> List[dict[str, Any]]:
    """Return tools whose name or description contains the query (case-insensitive)."""

    normalized = (query or "").strip().lower()
    if not normalized:
        return list(TOOLS)
    results: list[dict[str, Any]] = []
    for tool in TOOLS:
        name = str(tool.get("name", "")).lower()
        description = str(tool.get("description", "")).lower()
        if normalized in name or normalized in description:
            results.append(tool)
    return results


__all__ = ("TOOLS", "search_tools")
