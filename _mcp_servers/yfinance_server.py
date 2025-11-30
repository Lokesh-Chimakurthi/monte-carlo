#!/usr/bin/env python3
"""MCP Server for yfinance - Stock and Financial Data.

Provides tools for fetching stock prices, historical data, and financial metrics.
Designed for use with Monte Carlo simulations requiring real market data.

Usage:
    python yfinance_server.py

Or via stdio transport:
    uv run python _mcp_servers/yfinance_server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import yfinance as yf
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("yfinance")


def _safe_float(value: Any) -> float | None:
    """Convert value to float, returning None if not possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    """Convert value to int, returning None if not possible."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available yfinance tools."""
    return [
        Tool(
            name="get_stock_quote",
            description="Get current stock quote with price, volume, and basic metrics. Returns real-time market data for a given stock symbol.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'SBUX')",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_stock_history",
            description="Get historical stock price data for a given period. Useful for analyzing trends and volatility for Monte Carlo simulations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL', 'GOOGL')",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period for historical data",
                        "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
                        "default": "1y",
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data interval",
                        "enum": ["1d", "1wk", "1mo"],
                        "default": "1d",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_company_info",
            description="Get detailed company information including sector, industry, market cap, and financial ratios. Essential for business analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_financial_metrics",
            description="Get key financial metrics and ratios for fundamental analysis. Includes P/E ratio, profit margins, debt ratios, and growth rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="calculate_volatility",
            description="Calculate historical volatility (standard deviation of returns) for risk assessment in simulations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                    "period": {
                        "type": "string",
                        "description": "Period for volatility calculation",
                        "enum": ["1mo", "3mo", "6mo", "1y", "2y"],
                        "default": "1y",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_market_index",
            description="Get current data for major market indices (S&P 500, NASDAQ, Dow Jones, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Market index to fetch",
                        "enum": ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX"],
                        "default": "^GSPC",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="compare_stocks",
            description="Compare key metrics across multiple stocks for competitive analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols to compare (max 5)",
                    },
                },
                "required": ["symbols"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = await _execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute the specified tool with arguments."""
    if name == "get_stock_quote":
        return await _get_stock_quote(arguments["symbol"])
    elif name == "get_stock_history":
        return await _get_stock_history(
            arguments["symbol"],
            arguments.get("period", "1y"),
            arguments.get("interval", "1d"),
        )
    elif name == "get_company_info":
        return await _get_company_info(arguments["symbol"])
    elif name == "get_financial_metrics":
        return await _get_financial_metrics(arguments["symbol"])
    elif name == "calculate_volatility":
        return await _calculate_volatility(
            arguments["symbol"],
            arguments.get("period", "1y"),
        )
    elif name == "get_market_index":
        return await _get_market_index(arguments.get("index", "^GSPC"))
    elif name == "compare_stocks":
        symbols = arguments["symbols"][:5]  # Limit to 5
        return await _compare_stocks(symbols)
    else:
        return {"error": f"Unknown tool: {name}"}


async def _get_stock_quote(symbol: str) -> dict[str, Any]:
    """Get current stock quote."""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    return {
        "symbol": symbol.upper(),
        "name": info.get("shortName") or info.get("longName", "N/A"),
        "price": _safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
        "previous_close": _safe_float(info.get("previousClose")),
        "open": _safe_float(info.get("open") or info.get("regularMarketOpen")),
        "day_high": _safe_float(info.get("dayHigh") or info.get("regularMarketDayHigh")),
        "day_low": _safe_float(info.get("dayLow") or info.get("regularMarketDayLow")),
        "volume": _safe_int(info.get("volume") or info.get("regularMarketVolume")),
        "market_cap": _safe_int(info.get("marketCap")),
        "fifty_two_week_high": _safe_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _safe_float(info.get("fiftyTwoWeekLow")),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", "N/A"),
        "timestamp": datetime.now().isoformat(),
    }


async def _get_stock_history(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> dict[str, Any]:
    """Get historical stock data."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        return {"error": f"No historical data found for {symbol}"}

    # Convert to list of records
    records = []
    for date, row in hist.iterrows():
        records.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": _safe_float(row.get("Open")),
                "high": _safe_float(row.get("High")),
                "low": _safe_float(row.get("Low")),
                "close": _safe_float(row.get("Close")),
                "volume": _safe_int(row.get("Volume")),
            }
        )

    # Calculate summary statistics
    closes = [r["close"] for r in records if r["close"] is not None]

    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "data_points": len(records),
        "start_date": records[0]["date"] if records else None,
        "end_date": records[-1]["date"] if records else None,
        "summary": {
            "start_price": closes[0] if closes else None,
            "end_price": closes[-1] if closes else None,
            "min_price": min(closes) if closes else None,
            "max_price": max(closes) if closes else None,
            "avg_price": sum(closes) / len(closes) if closes else None,
            "total_return_pct": ((closes[-1] - closes[0]) / closes[0] * 100)
            if len(closes) >= 2
            else None,
        },
        "history": records[-30:],  # Last 30 data points to limit response size
    }


async def _get_company_info(symbol: str) -> dict[str, Any]:
    """Get detailed company information."""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    return {
        "symbol": symbol.upper(),
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "country": info.get("country", "N/A"),
        "website": info.get("website", "N/A"),
        "description": info.get("longBusinessSummary", "N/A")[:500] + "..."
        if info.get("longBusinessSummary")
        else "N/A",
        "employees": _safe_int(info.get("fullTimeEmployees")),
        "market_cap": _safe_int(info.get("marketCap")),
        "enterprise_value": _safe_int(info.get("enterpriseValue")),
        "revenue": _safe_int(info.get("totalRevenue")),
        "gross_profit": _safe_int(info.get("grossProfits")),
        "net_income": _safe_int(info.get("netIncomeToCommon")),
    }


async def _get_financial_metrics(symbol: str) -> dict[str, Any]:
    """Get key financial metrics and ratios."""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    return {
        "symbol": symbol.upper(),
        "valuation": {
            "pe_ratio": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "peg_ratio": _safe_float(info.get("pegRatio")),
            "price_to_book": _safe_float(info.get("priceToBook")),
            "price_to_sales": _safe_float(info.get("priceToSalesTrailing12Months")),
            "enterprise_to_revenue": _safe_float(info.get("enterpriseToRevenue")),
            "enterprise_to_ebitda": _safe_float(info.get("enterpriseToEbitda")),
        },
        "profitability": {
            "profit_margin": _safe_float(info.get("profitMargins")),
            "operating_margin": _safe_float(info.get("operatingMargins")),
            "gross_margin": _safe_float(info.get("grossMargins")),
            "return_on_equity": _safe_float(info.get("returnOnEquity")),
            "return_on_assets": _safe_float(info.get("returnOnAssets")),
        },
        "growth": {
            "revenue_growth": _safe_float(info.get("revenueGrowth")),
            "earnings_growth": _safe_float(info.get("earningsGrowth")),
            "earnings_quarterly_growth": _safe_float(info.get("earningsQuarterlyGrowth")),
        },
        "financial_health": {
            "current_ratio": _safe_float(info.get("currentRatio")),
            "quick_ratio": _safe_float(info.get("quickRatio")),
            "debt_to_equity": _safe_float(info.get("debtToEquity")),
            "total_debt": _safe_int(info.get("totalDebt")),
            "total_cash": _safe_int(info.get("totalCash")),
            "free_cash_flow": _safe_int(info.get("freeCashflow")),
        },
        "dividends": {
            "dividend_yield": _safe_float(info.get("dividendYield")),
            "dividend_rate": _safe_float(info.get("dividendRate")),
            "payout_ratio": _safe_float(info.get("payoutRatio")),
            "ex_dividend_date": str(info.get("exDividendDate"))
            if info.get("exDividendDate")
            else None,
        },
    }


async def _calculate_volatility(symbol: str, period: str = "1y") -> dict[str, Any]:
    """Calculate historical volatility."""
    import numpy as np

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)

    if hist.empty or len(hist) < 2:
        return {"error": f"Insufficient data for volatility calculation for {symbol}"}

    # Calculate daily returns
    closes = hist["Close"].values
    returns = np.diff(closes) / closes[:-1]

    # Calculate volatility metrics
    daily_volatility = float(np.std(returns))
    annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days

    return {
        "symbol": symbol.upper(),
        "period": period,
        "data_points": len(closes),
        "volatility": {
            "daily_std": daily_volatility,
            "annualized_std": annualized_volatility,
            "annualized_pct": annualized_volatility * 100,
        },
        "returns": {
            "mean_daily_return": float(np.mean(returns)),
            "mean_annual_return": float(np.mean(returns)) * 252,
            "min_daily_return": float(np.min(returns)),
            "max_daily_return": float(np.max(returns)),
        },
        "risk_metrics": {
            "sharpe_ratio_estimate": (float(np.mean(returns)) * 252) / annualized_volatility
            if annualized_volatility > 0
            else None,
            "var_95": float(np.percentile(returns, 5)),  # 95% VaR
            "var_99": float(np.percentile(returns, 1)),  # 99% VaR
        },
    }


async def _get_market_index(index: str = "^GSPC") -> dict[str, Any]:
    """Get market index data."""
    index_names = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ Composite",
        "^DJI": "Dow Jones Industrial Average",
        "^RUT": "Russell 2000",
        "^VIX": "CBOE Volatility Index",
    }

    ticker = yf.Ticker(index)
    info = ticker.info
    hist = ticker.history(period="5d")

    current_price = _safe_float(info.get("regularMarketPrice"))
    previous_close = _safe_float(info.get("previousClose"))

    return {
        "index": index,
        "name": index_names.get(index, index),
        "price": current_price,
        "previous_close": previous_close,
        "change": current_price - previous_close if current_price and previous_close else None,
        "change_pct": ((current_price - previous_close) / previous_close * 100)
        if current_price and previous_close
        else None,
        "day_high": _safe_float(info.get("regularMarketDayHigh")),
        "day_low": _safe_float(info.get("regularMarketDayLow")),
        "fifty_two_week_high": _safe_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _safe_float(info.get("fiftyTwoWeekLow")),
        "timestamp": datetime.now().isoformat(),
    }


async def _compare_stocks(symbols: list[str]) -> dict[str, Any]:
    """Compare multiple stocks."""
    comparisons = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            comparisons.append(
                {
                    "symbol": symbol.upper(),
                    "name": info.get("shortName", "N/A"),
                    "price": _safe_float(
                        info.get("currentPrice") or info.get("regularMarketPrice")
                    ),
                    "market_cap": _safe_int(info.get("marketCap")),
                    "pe_ratio": _safe_float(info.get("trailingPE")),
                    "profit_margin": _safe_float(info.get("profitMargins")),
                    "revenue_growth": _safe_float(info.get("revenueGrowth")),
                    "dividend_yield": _safe_float(info.get("dividendYield")),
                }
            )
        except Exception as e:
            comparisons.append(
                {
                    "symbol": symbol.upper(),
                    "error": str(e),
                }
            )

    return {
        "comparison": comparisons,
        "timestamp": datetime.now().isoformat(),
    }


async def main():
    """Run the MCP server."""
    logger.info("Starting yfinance MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
