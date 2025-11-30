"""Modal sandbox for secure code execution.

Each model (Claude, GPT, Gemini) gets its own persistent sandbox with:
- execute_python: IPython for stateful code execution
- execute_bash: Shell commands

Usage:
    from src.sandbox import Sandbox

    # Create per-model sandbox
    sandbox = await Sandbox.create("claude-session-123")

    # Execute Python (state persists)
    await sandbox.execute_python("x = 42")
    await sandbox.execute_python("print(x)")  # prints 42

    # Execute bash
    await sandbox.execute_bash("ls -la /mnt/servers")

    # Cleanup
    await sandbox.terminate()
"""

from src.sandbox.executor import (
    DEFAULT_TIMEOUT,
    ExecutionResult,
    Sandbox,
    run_bash,
    run_python,
)

__all__ = [
    "Sandbox",
    "ExecutionResult",
    "run_python",
    "run_bash",
    "DEFAULT_TIMEOUT",
]
