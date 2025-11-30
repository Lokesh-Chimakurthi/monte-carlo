"""Auto-generated TypedDict interfaces for yfinance MCP tools.

These interfaces provide type hints for tool parameters.
Import and use these for IDE autocompletion and type checking.
"""

from __future__ import annotations

from typing import Any, List, Optional, TypedDict, Literal

# Get current stock quote with price, volume, and basic metrics. Returns real-time market data for a given stock symbol.
class YfinanceGetStockQuoteInput(TypedDict):
    # Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'SBUX')
    symbol: str

# Get historical stock price data for a given period. Useful for analyzing trends and volatility for Monte Carlo simulations.
class YfinanceGetStockHistoryInput(TypedDict):
    # Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    symbol: str
    # Time period for historical data
    period: Optional[Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"]]
    # Data interval
    interval: Optional[Literal["1d", "1wk", "1mo"]]

# Get detailed company information including sector, industry, market cap, and financial ratios. Essential for business analysis.
class YfinanceGetCompanyInfoInput(TypedDict):
    # Stock ticker symbol
    symbol: str

# Get key financial metrics and ratios for fundamental analysis. Includes P/E ratio, profit margins, debt ratios, and growth rates.
class YfinanceGetFinancialMetricsInput(TypedDict):
    # Stock ticker symbol
    symbol: str

# Calculate historical volatility (standard deviation of returns) for risk assessment in simulations.
class YfinanceCalculateVolatilityInput(TypedDict):
    # Stock ticker symbol
    symbol: str
    # Period for volatility calculation
    period: Optional[Literal["1mo", "3mo", "6mo", "1y", "2y"]]

# Get current data for major market indices (S&P 500, NASDAQ, Dow Jones, etc.)
class YfinanceGetMarketIndexInput(TypedDict):
    # Market index to fetch
    index: Optional[Literal["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX"]]

# Compare key metrics across multiple stocks for competitive analysis.
class YfinanceCompareStocksInput(TypedDict):
    # List of stock ticker symbols to compare (max 5)
    symbols: List[str]

__all__ = ("YfinanceGetStockQuoteInput", "YfinanceGetStockHistoryInput", "YfinanceGetCompanyInfoInput", "YfinanceGetFinancialMetricsInput", "YfinanceCalculateVolatilityInput", "YfinanceGetMarketIndexInput", "YfinanceCompareStocksInput",)
