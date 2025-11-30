"""Modal Sandbox Executor - Simple per-model sandboxes.

Each model (Claude, GPT, Gemini) gets its own persistent sandbox with:
- execute_python: Persistent Python interpreter for stateful execution
- execute_bash: Shell commands

Usage:
    sandbox = await Sandbox.create("claude-session-123")
    result = await sandbox.execute_python("x = 42")
    result = await sandbox.execute_python("print(x)")  # x persists
    result = await sandbox.execute_bash("ls -la")
    await sandbox.terminate()
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import textwrap
from dataclasses import dataclass
from typing import Any, Final

import modal

APP_NAME: Final = "monte-carlo"
VOLUME_NAME: Final = "monte-carlo-mcp"
SERVERS_MOUNT: Final = "/mnt/servers"
DEFAULT_TIMEOUT: Final = 120  # 2 minutes per command

_PYTHON_SESSION_SCRIPT: Final = textwrap.dedent(
    """
    import contextlib
    import io
    import json
    import sys
    import traceback

    NAMESPACE = {}

    def run(code: str) -> dict:
        buffer_out = io.StringIO()
        buffer_err = io.StringIO()
        response = {"ok": True, "stdout": "", "stderr": ""}
        try:
            with contextlib.redirect_stdout(buffer_out), contextlib.redirect_stderr(buffer_err):
                exec(compile(code, "<sandbox>", "exec"), NAMESPACE, NAMESPACE)
        except Exception:  # noqa: BLE001 - propagate traceback to stderr
            response["ok"] = False
            traceback.print_exc(file=buffer_err)
        response["stdout"] = buffer_out.getvalue()
        response["stderr"] = buffer_err.getvalue()
        return response

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        if message.get("_terminate"):
            print(json.dumps({"ok": True, "stdout": "", "stderr": ""}), flush=True)
            break
        payload = run(message.get("code", ""))
        print(json.dumps(payload), flush=True)
    """
)

_PYTHON_SESSION_INIT: Final = textwrap.dedent(
    """
    import numpy as np
    import pandas as pd
    import json
    import sys
    sys.path.insert(0, '/mnt/servers')
    """
)


@dataclass(slots=True)
class ExecutionResult:
    """Result from code/command execution."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    error: str | None = None


def _build_image() -> modal.Image:
    """Build sandbox image with the runtime and dependencies we need."""
    return modal.Image.debian_slim(python_version="3.12").pip_install(
        # IPython remains available if needed for debugging
        "ipython>=8.0.0",
        # Data/simulation
        "numpy>=2.0.0",
        "pandas>=2.0.0",
        # Finance
        "yfinance>=0.2.66",
        # HTTP for MCP
        "httpx>=0.28.1",
        "aiohttp>=3.11.0",
        # MCP runtime
        "mcp>=1.22.0",
        "pydantic-ai-slim",
    )


class Sandbox:
    """Per-model sandbox with persistent Python and Bash execution."""

    def __init__(self, session_id: str, sandbox: modal.Sandbox) -> None:
        self.session_id = session_id
        self._sandbox = sandbox
        self._python_proc: Any | None = None

    @classmethod
    async def create(
        cls,
        session_id: str,
        timeout: int = 600,  # 10 min sandbox lifetime
    ) -> "Sandbox":
        """Create a new sandbox for a model session.

        Args:
            session_id: Unique ID (e.g., "claude-user123", "gpt-user123")
            timeout: Sandbox lifetime in seconds
        """
        app = modal.App.lookup(APP_NAME, create_if_missing=True)
        image = _build_image()

        # Get servers volume
        try:
            volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
            volumes = {SERVERS_MOUNT: volume}
        except Exception:  # noqa: BLE001 - fall back to ephemeral volume
            volumes = {}

        sb = await modal.Sandbox.create.aio(
            app=app,
            image=image,
            timeout=timeout,
            cpu=1.0,
            memory=2048,
            volumes=volumes,
        )

        return cls(session_id, sb)

    async def execute_python(
        self,
        code: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ExecutionResult:
        """Execute Python code in a persistent interpreter."""

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                await self._ensure_python_session(timeout)
                response = await self._communicate_with_python({"code": code}, timeout)
                return ExecutionResult(
                    success=bool(response.get("ok", False)),
                    stdout=response.get("stdout", ""),
                    stderr=response.get("stderr", ""),
                )
            except asyncio.TimeoutError:
                return ExecutionResult(success=False, error=f"Timeout after {timeout}s")
            except Exception as exc:  # noqa: BLE001 - surface sandbox errors
                last_error = exc
                await self._restart_python_session(timeout)

        error_message = str(last_error) if last_error else "Python session failed"
        return ExecutionResult(success=False, error=error_message)

    async def execute_bash(
        self,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ExecutionResult:
        """Execute a bash command inside the sandbox."""

        try:
            process = await self._sandbox.exec.aio(
                "bash",
                "-c",
                command,
                timeout=timeout,
            )
            stdout_bytes = await self._read_stream(process.stdout)
            stderr_bytes = await self._read_stream(process.stderr)
            await process.wait.aio()

            return ExecutionResult(
                success=getattr(process, "returncode", 0) == 0,
                stdout=self._decode_stream(stdout_bytes),
                stderr=self._decode_stream(stderr_bytes),
            )
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error=f"Timeout after {timeout}s",
            )
        except Exception as exc:  # noqa: BLE001 - surface sandbox errors
            return ExecutionResult(
                success=False,
                error=str(exc),
            )

    async def _ensure_python_session(self, timeout: int) -> None:
        """Start the persistent Python session if it is not running."""

        if self._python_proc is not None:
            return
        await self._start_python_session(timeout)

    async def _start_python_session(self, timeout: int) -> None:
        """Launch the long-lived Python interpreter process."""

        self._python_proc = await self._sandbox.exec.aio(
            "python3",
            "-u",
            "-c",
            _PYTHON_SESSION_SCRIPT,
            timeout=timeout,
        )
        await self._communicate_with_python({"code": _PYTHON_SESSION_INIT}, timeout)

    async def _restart_python_session(self, timeout: int) -> None:
        """Restart the Python session if it dies or becomes unhealthy."""

        await self._stop_python_session()
        await self._start_python_session(timeout)

    async def _communicate_with_python(
        self,
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        """Send a JSON payload to the Python session and await the response."""

        if self._python_proc is None:
            raise RuntimeError("Python session is not initialized")

        stdin = getattr(self._python_proc, "stdin", None)
        stdout = getattr(self._python_proc, "stdout", None)
        if stdin is None or stdout is None:
            raise RuntimeError("Python session streams are unavailable")

        message = json.dumps(payload).encode("utf-8") + b"\n"
        stdin.write(message)
        await stdin.drain.aio()

        try:
            line = await asyncio.wait_for(self._readline(stdout), timeout=timeout)
        except asyncio.TimeoutError:
            raise

        if not line:
            raise RuntimeError("Python session terminated unexpectedly")

        decoded = self._decode_stream(line).strip()
        if not decoded:
            return {"ok": True, "stdout": "", "stderr": ""}

        return json.loads(decoded)

    async def _read_stream(self, stream: Any) -> bytes | str:
        """Read from a sandbox stream, handling sync/async readers."""

        if stream is None:
            return b""
        read_fn = getattr(stream, "read", None)
        if read_fn is None:
            return b""
        data = read_fn()
        if inspect.isawaitable(data):
            return await data
        return data

    async def _readline(self, stream: Any) -> bytes | str:
        """Read a single line (best effort) from the sandbox stream."""

        if stream is None:
            return b""

        anext_fn = getattr(stream, "__anext__", None)
        if anext_fn is not None:
            try:
                return await anext_fn()
            except StopAsyncIteration:
                return b""

        aiter_fn = getattr(stream, "__aiter__", None)
        if aiter_fn is not None:
            iterator = aiter_fn()
            anext_fn = getattr(iterator, "__anext__", None)
            if anext_fn is not None:
                try:
                    return await anext_fn()
                except StopAsyncIteration:
                    return b""

        readline_fn = getattr(stream, "readline", None)
        if readline_fn is not None:
            data = readline_fn()
            if inspect.isawaitable(data):
                return await data
            return data

        return await self._read_stream(stream)

    async def _stop_python_session(self) -> None:
        """Stop the persistent Python process if it is running."""

        if self._python_proc is None:
            return

        stdin = getattr(self._python_proc, "stdin", None)
        stdout = getattr(self._python_proc, "stdout", None)
        try:
            if stdin is not None:
                stdin.write(b'{"_terminate": true}\n')
                await stdin.drain.aio()
            if stdout is not None:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self._readline(stdout), timeout=5)
        except Exception:  # noqa: BLE001 - best effort shutdown
            pass
        finally:
            with contextlib.suppress(Exception):
                await self._python_proc.wait.aio()
            self._python_proc = None

    @staticmethod
    def _decode_stream(data: bytes | bytearray | str | None) -> str:
        """Decode sandbox stream data into text."""

        if data is None:
            return ""
        if isinstance(data, (bytes, bytearray)):
            return data.decode("utf-8", errors="ignore")
        return data

    async def terminate(self) -> None:
        """Terminate the sandbox."""
        await self._stop_python_session()
        await self._sandbox.terminate.aio()

    @property
    def object_id(self) -> str:
        """Get sandbox ID for later retrieval."""
        return self._sandbox.object_id


# Convenience functions for one-off execution
async def run_python(code: str, session_id: str = "default") -> ExecutionResult:
    """Run Python code in a temporary sandbox."""
    sandbox = await Sandbox.create(session_id)
    try:
        return await sandbox.execute_python(code)
    finally:
        await sandbox.terminate()


async def run_bash(command: str, session_id: str = "default") -> ExecutionResult:
    """Run bash command in a temporary sandbox."""
    sandbox = await Sandbox.create(session_id)
    try:
        return await sandbox.execute_bash(command)
    finally:
        await sandbox.terminate()
