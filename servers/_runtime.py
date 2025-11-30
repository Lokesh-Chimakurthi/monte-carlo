"""Runtime helpers for generated MCP tool wrappers.

The helper locates connection details via environment variables.

Variable naming pattern (provider slug uppercased, non-alphanumerics replaced with `_`):
- MCP_SERVER_<PROVIDER>_TRANSPORT: `http` (default) or `stdio`.
- MCP_SERVER_<PROVIDER>_URL: HTTP endpoint for Streamable HTTP servers.
- MCP_SERVER_<PROVIDER>_HEADERS: Optional JSON object or comma-separated KEY=VALUE list.
- MCP_SERVER_<PROVIDER>_COMMAND: Executable for stdio transports.
- MCP_SERVER_<PROVIDER>_ARGS: Optional JSON array or comma-separated arg list.
- MCP_SERVER_<PROVIDER>_ENV: Optional JSON object / KEY=VALUE list for env vars.
- MCP_SERVER_<PROVIDER>_CWD: Working directory for stdio transports.
- MCP_SERVER_<PROVIDER>_TIMEOUT: Connection timeout seconds (defaults to 30).
- MCP_SERVER_<PROVIDER>_READ_TIMEOUT: Read timeout seconds (defaults to 300).

Omit the provider segment to define global defaults (e.g., MCP_SERVER_URL).
"""

from __future__ import annotations

import importlib
import json
import os
import re
from typing import Any

from pydantic_ai.mcp import MCPServer, MCPServerStdio, MCPServerStreamableHTTP

_CONFIG_PREFIX = "MCP_SERVER"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_READ_TIMEOUT = 300.0

_SERVER_CACHE: dict[str, tuple[str, MCPServer]] = {}
_STATIC_CONFIG_CACHE: dict[str, dict[str, Any]] = {}


async def call_tool(provider: str, tool: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
    """Call the MCP tool described by ``tool`` for ``provider``."""
    payload = _coerce_arguments(args, kwargs)
    tool_name = tool.get("name")
    if not tool_name:
        raise ValueError("tool definition must include a 'name' field")
    server = _get_server(provider)
    return await server.direct_call_tool(tool_name, payload)


def _coerce_arguments(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    if args and kwargs:
        raise ValueError("Pass arguments either positionally (single dict) or via kwargs, not both.")
    if not args:
        return dict(kwargs)
    if len(args) != 1:
        raise TypeError("Pass a single dictionary positional argument or use keyword arguments.")
    payload = args[0]
    if not isinstance(payload, dict):
        raise TypeError("Positional tool arguments must be provided as a dict")
    return dict(payload)


def _get_server(provider: str) -> MCPServer:
    config = _load_provider_config(provider)
    fingerprint = json.dumps(config, sort_keys=True)
    cached = _SERVER_CACHE.get(provider)
    if cached and cached[0] == fingerprint:
        return cached[1]
    server = _build_server(config)
    _SERVER_CACHE[provider] = (fingerprint, server)
    return server


def _build_server(config: dict[str, Any]) -> MCPServer:
    transport = config["transport"]
    if transport == "http":
        return MCPServerStreamableHTTP(
            config["url"],
            headers=config.get("headers"),
            timeout=config["timeout"],
            read_timeout=config["read_timeout"],
        )
    if transport == "stdio":
        return MCPServerStdio(
            config["command"],
            args=config.get("args"),
            env=config.get("env"),
            cwd=config.get("cwd"),
            timeout=config["timeout"],
            read_timeout=config["read_timeout"],
        )
    raise RuntimeError(f"Unsupported MCP transport: {transport}")


def _load_provider_config(provider: str) -> dict[str, Any]:
    static_config = _load_static_config(provider)
    provider_key = _normalize_provider(provider)
    timeout = _as_float(
        _get_env(provider_key, "TIMEOUT"),
        _as_float(_get_env("", "TIMEOUT"), static_config.get("timeout", _DEFAULT_TIMEOUT)),
    )
    read_timeout = _as_float(
        _get_env(provider_key, "READ_TIMEOUT"),
        _as_float(_get_env("", "READ_TIMEOUT"), static_config.get("read_timeout", _DEFAULT_READ_TIMEOUT)),
    )
    transport = (
        _get_env(provider_key, "TRANSPORT")
        or _get_env("", "TRANSPORT")
        or static_config.get("transport")
        or "http"
    ).lower()

    if transport == "http":
        url = _get_env(provider_key, "URL") or _get_env("", "URL") or static_config.get("url")
        if not url:
            raise RuntimeError(
                f"Missing MCP server URL for provider '{provider}'. Set MCP_SERVER_<PROVIDER>_URL or MCP_SERVER_URL."
            )
        headers = _parse_mapping(_get_env(provider_key, "HEADERS") or _get_env("", "HEADERS"))
        if headers is None:
            headers = static_config.get("headers")
        return {
            "transport": "http",
            "url": url,
            "headers": headers,
            "timeout": timeout,
            "read_timeout": read_timeout,
        }

    if transport == "stdio":
        command = _get_env(provider_key, "COMMAND") or _get_env("", "COMMAND") or static_config.get("command")
        if not command:
            raise RuntimeError(
                f"Missing MCP server command for provider '{provider}'. Set MCP_SERVER_<PROVIDER>_COMMAND."
            )
        args = _parse_sequence(_get_env(provider_key, "ARGS") or _get_env("", "ARGS"))
        if not args:
            args = list(static_config.get("args") or [])
        env = _parse_mapping(_get_env(provider_key, "ENV") or _get_env("", "ENV"))
        if env is None:
            env = static_config.get("env")
        cwd = _get_env(provider_key, "CWD") or _get_env("", "CWD") or static_config.get("cwd")
        return {
            "transport": "stdio",
            "command": command,
            "args": args,
            "env": env,
            "cwd": cwd,
            "timeout": timeout,
            "read_timeout": read_timeout,
        }

    raise RuntimeError(
        f"Unsupported MCP transport '{transport}' for provider '{provider}'. Use 'http' or 'stdio'."
    )


def _load_static_config(provider: str) -> dict[str, Any]:
    cached = _STATIC_CONFIG_CACHE.get(provider)
    if cached is not None:
        return dict(cached)
    module_name = f"{__package__}.{provider}" if __package__ else provider
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        config: dict[str, Any] = {}
    else:
        config = getattr(module, "SERVER_CONFIG", {}) or {}
    _STATIC_CONFIG_CACHE[provider] = dict(config)
    return dict(config)


def _normalize_provider(provider: str) -> str:
    normalized = re.sub(r"[^0-9A-Z]+", "_", provider.upper()).strip("_")
    return normalized


def _get_env(provider_key: str, suffix: str) -> str | None:
    if provider_key:
        scoped = os.getenv(f"{_CONFIG_PREFIX}_{provider_key}_{suffix}")
        if scoped:
            return scoped
    return os.getenv(f"{_CONFIG_PREFIX}_{suffix}")


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid float value '{value}'") from exc


def _parse_mapping(value: str | None) -> dict[str, str] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if parsed is None:
        items: dict[str, str] = {}
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            key, sep, val = part.partition("=")
            if not sep:
                raise ValueError(
                    "Mapping values must be JSON objects or comma-separated KEY=VALUE entries"
                )
            items[key.strip()] = val.strip()
        return items or None
    if not isinstance(parsed, dict):
        raise ValueError("Mapping values must be JSON objects or comma-separated KEY=VALUE entries")
    return {str(key): str(val) for key, val in parsed.items()}


def _parse_sequence(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    if isinstance(parsed, str):
        return [parsed]
    if parsed is not None:
        raise ValueError("Sequence values must be JSON arrays, strings, or comma/space separated text")
    parts = [segment.strip() for segment in value.replace(",", " ").split() if segment.strip()]
    return parts
