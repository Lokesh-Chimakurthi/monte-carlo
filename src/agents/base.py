"""Base Agent with sandbox execution tools.

Simple agent that can be configured for different models (Claude, GPT, Gemini).
Each agent gets its own Modal sandbox with persistent IPython + Bash.

Usage:
    # For Claude (using Agent SDK)
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    from src.agents import create_sandbox_server

    sandbox = create_sandbox_server("user-123")
    options = ClaudeAgentOptions(
        _mcp_servers={"sandbox": sandbox},
        allowed_tools=["mcp__sandbox__execute_python", "mcp__sandbox__execute_bash"],
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Run a Monte Carlo simulation")
        async for msg in client.receive_response():
            print(msg)
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from src.sandbox import Sandbox

# Global sandbox registry for tool handlers
_sandboxes: dict[str, Sandbox] = {}


async def _get_sandbox(session_id: str) -> Sandbox:
    """Get or create sandbox for session."""
    if session_id not in _sandboxes:
        _sandboxes[session_id] = await Sandbox.create(session_id)
    return _sandboxes[session_id]


async def cleanup_sandbox(session_id: str) -> None:
    """Terminate and remove sandbox."""
    if session_id in _sandboxes:
        await _sandboxes[session_id].terminate()
        del _sandboxes[session_id]


def create_sandbox_tools(session_id: str):
    """Create execute_python and execute_bash tools for a session.

    Args:
        session_id: Unique session ID for sandbox isolation

    Returns:
        Tuple of (execute_python_tool, execute_bash_tool)
    """

    @tool(
        "execute_python",
        "Execute Python code in a persistent Modal IPython environment. Variables and imports persist across calls. numpy, pandas, scipy, yfinance are available. Use print() to see output.",
        {"code": str},
    )
    async def execute_python(args: dict[str, Any]) -> dict[str, Any]:
        sandbox = await _get_sandbox(session_id)
        result = await sandbox.execute_python(args["code"])

        output = result.stdout or ""
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.error:
            output = f"Error: {result.error}"

        out = {
            "content": [{"type": "text", "text": output or "(no output)"}],
            "is_error": bool(result.error),
        }
        print(out)
        return out

    @tool(
        "execute_bash",
        "Execute a bash command in the Modal sandbox. Use for file operations and system commands.",
        {"command": str},
    )
    async def execute_bash(args: dict[str, Any]) -> dict[str, Any]:
        sandbox = await _get_sandbox(session_id)
        result = await sandbox.execute_bash(args["command"])

        output = result.stdout or ""
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.error:
            output = f"Error: {result.error}"

        out = {
            "content": [{"type": "text", "text": output or "(no output)"}],
            "is_error": bool(result.error),
        }
        print(out)
        return out

    return execute_python, execute_bash


def create_sandbox_server(session_id: str, name: str = "sandbox"):
    """Create an MCP server with sandbox tools for Claude Agent SDK.

    Args:
        session_id: Unique session ID for sandbox isolation
        name: Server name (default: "sandbox")

    Returns:
        McpSdkServerConfig for use with ClaudeAgentOptions
    """
    execute_python, execute_bash = create_sandbox_tools(session_id)

    return create_sdk_mcp_server(
        name=name,
        version="1.0.0",
        tools=[execute_python, execute_bash],
    )
