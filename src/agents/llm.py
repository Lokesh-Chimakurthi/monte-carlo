"""Simple agent factory for multi-model support.

Usage:
    from src.agents import get_agent

    # Get agent for any model
    async with get_agent("claude", session_id="user-123") as client:
        await client.query("Run a simulation")
        async for msg in client.receive_response():
            print(msg)

    # Or use specific model versions
    async with get_agent("gpt-4o", session_id="user-456") as client:
        ...
"""

from __future__ import annotations

from typing import Literal

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from src.agents.base import create_sandbox_server

# Model aliases -> actual model names
MODEL_MAP: dict[str, str] = {
    # Claude models
    "claude": "claude-sonnet-4.5",
    "claude-opus": "claude-opus-4.5",
    "claude-haiku": "claude-haiku-4.5",
    # GPT models (via Claude SDK)
    "gpt": "gpt-5.1",
    "gpt-4.1": "gpt-4.1",
    # Gemini models (via Claude SDK)
    "gemini": "gemini-3-pro-preview",
    "gemini-2.5": "gemini-2.5-pro",
}

ModelName = Literal[
    "claude",
    "claude-opus",
    "claude-haiku",
    "gpt",
    "gpt-4.1",
    "gemini",
    "gemini-2.5",
]

# System prompt for MCP Code Mode agents
SYSTEM_PROMPT = """<role>
You are a Monte Carlo Oracle agent. You answer "what if" questions by gathering real-world data via MCP tools, then running thousands of simulations to produce probability distributions.
</role>

<tools>
execute_python: Run Python in a persistent session. Variables and imports persist across calls.
execute_bash: Run shell commands.
</tools>

<mcp_discovery>
MCP tool clients are at /mnt/servers/. Follow this 4-step discovery pattern:

STEP 1 - List available servers:
```python
import os
servers = [s for s in os.listdir('/mnt/servers') if not s.startswith('_')]
print("Available servers:", servers)
```

STEP 2 - Check a server's tools (read its __init__.py):
```python
tools = [s for s in os.listdir('/mnt/servers/SERVER_NAME') if not s.startswith('_')]
    print(tools)
```

STEP 3 - Get tool interface (read the tool module):
```python
with open('/mnt/servers/SERVER_NAME/TOOL_NAME.py') as f:
    print(f.read())  # Shows function signature, params, return type
```

STEP 4 - Import and call the tool:
```python
import sys
sys.path.insert(0, '/mnt/servers')
import asyncio
from servers.SERVER_NAME import tool_name

result = asyncio.run(tool_name(param="value"))
print(result)
```

Key: Discover first, then use. Never guess tool names or parameters.
</mcp_discovery>

<packages>
These packages are available at startup: numpy, pandas, scipy, yfinance, httpx, aiohttp, plotly
</packages>

<workflow>
1. DISCOVER: List servers, find relevant tools for the question
2. RESEARCH: Call MCP tools to gather real-world data
3. MODEL: Build probability distributions from research
4. SIMULATE: Run 10,000 Monte Carlo iterations (vectorized numpy)
5. REPORT: Return statistics, confidence intervals, recommendation
</workflow>

<rules>
- Always discover tools before using them
- Process data in sandbox, return only summaries
- Never print raw API responses or large datasets
- Use variables to store intermediate results and for downstream steps
- Use print() for all output
</rules>"""


def get_agent(
    model: ModelName | str,
    session_id: str,
    *,
    system_prompt: str | None = None,
) -> ClaudeSDKClient:
    """Get an agent for the specified model with sandbox tools.

    Args:
        model: Model name (e.g., "claude", "gpt", "gemini")
        session_id: Unique session ID for sandbox isolation
        system_prompt: Optional system prompt override

    Returns:
        ClaudeSDKClient configured for the model with sandbox tools
    """
    model_id = MODEL_MAP.get(model, model)
    sandbox = create_sandbox_server(session_id)

    options = ClaudeAgentOptions(
        model=model_id,
        mcp_servers={"sandbox": sandbox},
        allowed_tools=["mcp__sandbox__execute_python", "mcp__sandbox__execute_bash"],
        system_prompt=system_prompt or SYSTEM_PROMPT,
        disallowed_tools=[
            "Bash",
            "Edit",
            "Read",
            "write",
            "Glob",
            "NotebookEdit",
            "WebFetch",
            "WebSearch",
            "BashOutput",
            "KillBash",
        ],
    )

    return ClaudeSDKClient(options=options)
