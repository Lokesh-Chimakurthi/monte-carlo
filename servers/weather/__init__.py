"""Auto-generated tool package for weather.

Usage:
    from servers.weather import <tool_function>

Example:
    from servers.weather import get_current_weather
    result = await get_current_weather(param=value)
"""

from __future__ import annotations

from . import get_current_weather as _get_current_weather_module
from . import get_weather_forecast as _get_weather_forecast_module
from . import get_hourly_forecast as _get_hourly_forecast_module
from . import get_historical_weather as _get_historical_weather_module
from . import get_climate_averages as _get_climate_averages_module
from . import get_weather_statistics as _get_weather_statistics_module

# Re-export tool functions for convenient imports
from .get_current_weather import get_current_weather
from .get_weather_forecast import get_weather_forecast
from .get_hourly_forecast import get_hourly_forecast
from .get_historical_weather import get_historical_weather
from .get_climate_averages import get_climate_averages
from .get_weather_statistics import get_weather_statistics
from . import manifest

# Non-sensitive defaults for this provider.
SERVER_CONFIG = {'args': ['run', 'python', '_mcp_servers/weather_server.py'], 'command': 'uv', 'cwd': None, 'read_timeout': 30.0, 'timeout': 30.0, 'transport': 'stdio'}

__all__ = ("get_current_weather", "get_weather_forecast", "get_hourly_forecast", "get_historical_weather", "get_climate_averages", "get_weather_statistics", "manifest", "SERVER_CONFIG",)
