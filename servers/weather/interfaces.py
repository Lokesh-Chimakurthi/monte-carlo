"""Auto-generated TypedDict interfaces for weather MCP tools.

These interfaces provide type hints for tool parameters.
Import and use these for IDE autocompletion and type checking.
"""

from __future__ import annotations

from typing import Any, List, Optional, TypedDict, Literal

# Get current weather conditions for a location. Returns temperature, humidity, wind, and conditions.
class WeatherGetCurrentWeatherInput(TypedDict):
    # City name or location (e.g., 'Seattle', 'New York', 'London, UK')
    location: str

# Get weather forecast for the next 7 days. Includes daily high/low temperatures, precipitation probability, and conditions.
class WeatherGetWeatherForecastInput(TypedDict):
    # City name or location
    location: str
    # Number of forecast days (1-16)
    days: Optional[int]

# Get detailed hourly weather forecast for the next 48 hours. Useful for short-term planning.
class WeatherGetHourlyForecastInput(TypedDict):
    # City name or location
    location: str

# Get historical weather data for a specific date range. Useful for analyzing seasonal patterns and trends.
class WeatherGetHistoricalWeatherInput(TypedDict):
    # City name or location
    location: str
    # Start date in YYYY-MM-DD format
    start_date: str
    # End date in YYYY-MM-DD format
    end_date: str

# Get climate averages and typical weather patterns for a location. Based on historical data analysis.
class WeatherGetClimateAveragesInput(TypedDict):
    # City name or location
    location: str

# Get weather statistics for Monte Carlo simulations - temperature ranges, precipitation patterns, and seasonal variations.
class WeatherGetWeatherStatisticsInput(TypedDict):
    # City name or location
    location: str
    # Weather metric to analyze
    metric: Optional[Literal["temperature", "precipitation", "sunshine", "wind"]]

__all__ = ("WeatherGetCurrentWeatherInput", "WeatherGetWeatherForecastInput", "WeatherGetHourlyForecastInput", "WeatherGetHistoricalWeatherInput", "WeatherGetClimateAveragesInput", "WeatherGetWeatherStatisticsInput",)
