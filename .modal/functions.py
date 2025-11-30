"""Base Modal configuration for sandboxed MCP code execution."""

from __future__ import annotations

from typing import Final

import modal

APP_NAME: Final = "monte-carlo"
SERVERS_MOUNT: Final = "/mnt/servers"
WORKSPACE_ROOT: Final = "/workspace"


def build_sandbox_image() -> modal.Image:
    """Return the shared Modal image used by sandbox runs."""
    return modal.Image.debian_slim(python_version="3.12").uv_pip_install(
        # AI Models
        "anthropic>=0.75.0",
        "claude-agent-sdk>=0.1.10",
        "google-genai>=1.52.0",
        "openai>=2.8.1",
        # MCP & Tools
        "mcp>=1.22.0",
        "pydantic-ai-slim>=1.25.1",
        "tavily-python>=0.5.0",
        # Sandbox & Execution
        "modal>=1.2.4",
        # UI & Visualization
        "gradio>=6.0.1",
        "plotly>=6.5.0",
        # Data & Finance
        "yfinance>=0.2.66",
        "numpy>=2.0.0",
        "pandas>=2.0.0",
        # HTTP & Utils
        "httpx>=0.28.1",
        "python-dotenv>=1.0.0",
    )


def workspace_volume(session_id: str) -> modal.Volume:
    """Allocate or fetch a per-session workspace volume."""
    return modal.Volume.from_name(
        f"hackathon-workspace-{session_id}",
        create_if_missing=True,
    )


def servers_volume() -> modal.Volume:
    """Return the shared read-only servers manifest volume."""
    return modal.Volume.from_name(
        "monte-carlo-mcp",
        create_if_missing=True,
    )


def required_secret_names() -> list[str]:
    """List secrets that must exist inside the Modal workspace."""
    return [
        "anthropic-api-key",
        "tavily-api-key",
    ]
