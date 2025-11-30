"""CLI that snapshots MCP tool definitions into local files (optional Modal upload)."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import re
import shutil
import textwrap
from pathlib import Path
from typing import Any, Iterable

from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP

DEFAULT_OUTPUT_DIR = Path("servers")
RUNTIME_MODULE_NAME = "_runtime.py"


def parse_args() -> argparse.Namespace:
    """Configure top-level argument parsing."""

    parser = argparse.ArgumentParser(
        description="Fetch MCP tools at runtime and dump them to local files.",
    )
    parser.add_argument(
        "--provider",
        required=True,
        help="Provider slug used for the output folder (e.g., gmail, baserow).",
    )
    parser.add_argument(
        "--provider-title",
        help="Optional human-readable title to store in docstrings.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Base directory where tool folders are created (default: ./servers).",
    )
    parser.add_argument(
        "--modal-upload",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Upload the generated folder to the shared Modal volume.",
    )

    subparsers = parser.add_subparsers(
        required=True,
        dest="transport",
        help="MCP transport selection",
    )

    http_parser = subparsers.add_parser("http", help="Connect to an MCP Streamable HTTP endpoint.")
    http_parser.add_argument("--url", required=True, help="MCP messages endpoint.")
    http_parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Additional HTTP header in KEY=VALUE form (repeatable).",
    )
    http_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout (seconds).",
    )
    http_parser.add_argument(
        "--read-timeout",
        type=float,
        default=300.0,
        help="SSE/read timeout (seconds).",
    )

    stdio_parser = subparsers.add_parser(
        "stdio", help="Spawn a local MCP server process over stdio."
    )
    stdio_parser.add_argument(
        "--command", required=True, help="Executable to launch (e.g., uv, node)."
    )
    stdio_parser.add_argument(
        "--args",
        nargs="*",
        default=[],
        help="Arguments passed to the executable.",
    )
    stdio_parser.add_argument(
        "--env",
        action="append",
        default=[],
        help="Environment variable KEY=VALUE pairs (repeatable).",
    )
    stdio_parser.add_argument("--cwd", help="Working directory for the spawned process.")
    stdio_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Process request timeout (seconds).",
    )
    stdio_parser.add_argument(
        "--read-timeout",
        type=float,
        default=30.0,
        help="Read timeout for stdio transport (seconds).",
    )

    return parser.parse_args()


async def fetch_tools(
    args: argparse.Namespace,
) -> tuple[Iterable[Any], str, dict[str, Any], dict[str, str]]:
    """Instantiate the requested MCP transport and list tools."""

    transport_config: dict[str, Any]
    secret_env: dict[str, str] = {}
    env_prefix = _provider_env_prefix(args.provider)

    if args.transport == "http":
        headers = _parse_key_values(args.header, "header")
        server = MCPServerStreamableHTTP(
            args.url,
            headers=headers or None,
            timeout=args.timeout,
            read_timeout=args.read_timeout,
        )
        transport_config = {
            "transport": "http",
            "url": args.url,
            "timeout": args.timeout,
            "read_timeout": args.read_timeout,
        }
        if headers:
            secret_env[f"MCP_SERVER_{env_prefix}_HEADERS"] = json.dumps(
                headers, separators=(",", ":")
            )
    elif args.transport == "stdio":
        env = _parse_key_values(args.env, "env")
        server = MCPServerStdio(
            args.command,
            args=args.args,
            env=env or None,
            cwd=args.cwd,
            timeout=args.timeout,
            read_timeout=args.read_timeout,
        )
        transport_config = {
            "transport": "stdio",
            "command": args.command,
            "args": list(args.args or []),
            "cwd": args.cwd,
            "timeout": args.timeout,
            "read_timeout": args.read_timeout,
        }
        if env:
            secret_env[f"MCP_SERVER_{env_prefix}_ENV"] = json.dumps(env, separators=(",", ":"))
    else:  # pragma: no cover - guarded by argparse
        raise ValueError(f"Unsupported transport: {args.transport}")

    tools = list(await server.list_tools())
    info_name = None
    if hasattr(server, "server_info") and server.server_info is not None:
        info_name = getattr(server.server_info, "name", None)
    server_name = args.provider_title or info_name or args.provider
    return tools, server_name, transport_config, secret_env


def sync_to_disk(
    provider: str,
    provider_title: str,
    tools: Iterable[Any],
    output_dir: Path,
    transport_config: dict[str, Any],
) -> tuple[Path, int]:
    """Write each tool definition to disk as a minimal Python module."""

    base_dir = output_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    _write_runtime_module(base_dir)
    root_init = base_dir / "__init__.py"
    if not root_init.exists():
        root_init.write_text('"""MCP tool packages."""\n', encoding="utf-8")

    provider_dir = base_dir / provider
    if provider_dir.exists():
        shutil.rmtree(provider_dir)
    provider_dir.mkdir(parents=True, exist_ok=True)

    module_names: list[str] = []
    tool_entries: list[dict[str, Any]] = []
    for tool in tools:
        module_name = _slugify(tool.name)
        module_path = provider_dir / f"{module_name}.py"
        tool_data = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
        module_content = _render_tool_module(provider, provider_title, tool_data)
        module_path.write_text(module_content, encoding="utf-8")
        module_names.append(module_name)
        tool_entries.append(tool_data)

    (provider_dir / "__init__.py").write_text(
        _render_provider_init(provider, provider_title, module_names, transport_config),
        encoding="utf-8",
    )
    _write_manifest(provider_dir, provider, tool_entries)
    _write_interfaces(provider_dir, provider, tool_entries)

    return provider_dir, len(module_names)


def maybe_upload_to_modal(base_dir: Path, provider_dir: Path, provider: str) -> None:
    """Copy the generated provider folder into the shared Modal volume."""

    config_path = Path(".modal/functions.py").resolve()
    if not config_path.exists():
        raise FileNotFoundError("Modal configuration (.modal/functions.py) not found.")

    spec = importlib.util.spec_from_file_location("modal_functions", config_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError("Unable to import Modal configuration module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    volume = module.servers_volume()
    remote_root = f"/{provider}"
    try:
        volume.remove_file(remote_root, recursive=True)
    except Exception:
        pass

    base_root = base_dir.resolve()
    runtime_path = base_root / RUNTIME_MODULE_NAME

    with volume.batch_upload(force=True) as batch:
        batch.put_directory(str(provider_dir), remote_root)
        if runtime_path.exists():
            batch.put_file(str(runtime_path), "/_runtime.py")

    # Also write and upload the code_mode helpers
    _write_and_upload_code_mode_helpers(volume, base_dir)


def _write_and_upload_code_mode_helpers(volume: Any, base_dir: Path) -> None:
    """Write and upload code_mode helper module to Modal volume.

    This creates a standalone _code_mode.py that can be imported in the sandbox
    for progressive tool discovery and interface generation.
    """
    code_mode_content = _render_code_mode_helper()
    local_path = base_dir / "_code_mode.py"
    local_path.write_text(code_mode_content, encoding="utf-8")

    with volume.batch_upload(force=True) as batch:
        batch.put_file(str(local_path), "/_code_mode.py")

    print("Uploaded code_mode helper to Modal volume.")


def _render_code_mode_helper() -> str:
    """Generate standalone code_mode helper for sandbox use."""
    return textwrap.dedent('''\
        """MCP Code Mode helpers for progressive tool discovery.

        This module provides token-efficient tool discovery for sandboxed code execution.
        Import it in the sandbox to search tools and get TypedDict interfaces.

        Usage in sandbox:
            import sys
            sys.path.append('/mnt/servers')
            from _code_mode import search_tools, get_tool_interface, list_providers

            # Discover tools efficiently
            tools = search_tools("email", limit=5)
            interface = get_tool_interface("gmail", "GMAIL_SEND_EMAIL")
        """

        from __future__ import annotations

        import importlib.util
        import json
        import re
        from pathlib import Path
        from typing import Any, TypedDict


        class ToolSearchResult(TypedDict):
            """Result from searching available tools."""
            provider: str
            name: str
            description: str
            function_name: str


        class ToolInterface(TypedDict):
            """Full tool interface with schema."""
            provider: str
            name: str
            description: str
            function_name: str
            input_schema: dict[str, Any]
            python_interface: str


        # Default servers path in Modal sandbox
        DEFAULT_SERVERS_PATH = Path("/mnt/servers")


        def _matches_query(query_words: list[str], text: str) -> bool:
            """Check if ALL query words are found in text (word-based matching).

            This handles queries like 'search web' matching 'search the web'.
            """
            text_lower = text.lower()
            return all(word in text_lower for word in query_words)


        def search_tools(
            query: str,
            servers_path: str | Path = DEFAULT_SERVERS_PATH,
            limit: int = 10,
        ) -> list[ToolSearchResult]:
            """Search available MCP tools by name or description.

            Uses word-based matching: 'search web' matches 'search the web'.
            All query words must be present (AND logic).

            Args:
                query: Search query (space-separated words, case-insensitive).
                servers_path: Path to servers directory.
                limit: Maximum results to return.

            Returns:
                List of matching tools with basic metadata.
            """
            servers_path = Path(servers_path)
            if not servers_path.exists():
                return []

            # Split query into words for flexible matching
            query_words = [w.lower() for w in query.strip().split() if w]
            results: list[ToolSearchResult] = []

            for provider_path in sorted(servers_path.iterdir()):
                if not provider_path.is_dir() or provider_path.name.startswith("_"):
                    continue

                manifest_path = provider_path / "manifest.py"
                if not manifest_path.exists():
                    continue

                try:
                    tools = _load_manifest_tools(provider_path.name, servers_path)
                    for tool in tools:
                        name = str(tool.get("name", ""))
                        description = str(tool.get("description", ""))
                        combined = f"{name} {description}"

                        # Match if no query OR all query words found
                        if not query_words or _matches_query(query_words, combined):
                            results.append(
                                ToolSearchResult(
                                    provider=provider_path.name,
                                    name=name,
                                    description=_truncate(description),
                                    function_name=_slugify(name),
                                )
                            )
                            if len(results) >= limit:
                                return results
                except Exception:
                    continue

            return results


        def list_providers(servers_path: str | Path = DEFAULT_SERVERS_PATH) -> list[str]:
            """List all available MCP providers."""
            servers_path = Path(servers_path)
            if not servers_path.exists():
                return []

            return [
                p.name for p in sorted(servers_path.iterdir())
                if p.is_dir() and not p.name.startswith("_") and (p / "__init__.py").exists()
            ]


        def get_tool_interface(
            provider: str,
            tool_name: str,
            servers_path: str | Path = DEFAULT_SERVERS_PATH,
        ) -> dict[str, Any] | None:
            """Get clean interface for a specific tool - ready to use.

            Returns only what you need:
            - import_statement: Copy-paste import
            - function_name: The callable function
            - parameters: TypedDict showing required params
            - example: Ready-to-run code

            Args:
                provider: Provider name (e.g., 'gmail').
                tool_name: Tool name from search results.
                servers_path: Path to servers directory.

            Returns:
                Clean interface dict or None if not found.
            """
            servers_path = Path(servers_path)
            tools = _load_manifest_tools(provider, servers_path)

            for tool in tools:
                if tool.get("name") == tool_name:
                    input_schema = tool.get("inputSchema", {})
                    func_name = _slugify(tool_name)
                    typed_dict = _generate_typed_dict(provider, tool_name, input_schema)
                    example = _generate_example(provider, func_name, input_schema)

                    return {
                        "import": f"from servers.{provider} import {func_name}",
                        "function": func_name,
                        "description": _truncate(tool.get("description", ""), 200),
                        "parameters": typed_dict,
                        "example": example,
                    }
            return None


        def _generate_example(provider: str, func_name: str, schema: dict[str, Any]) -> str:
            """Generate example code for calling the tool."""
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))

            args = []
            for prop, prop_schema in properties.items():
                if prop in required:
                    example_val = _get_example_value(prop_schema)
                    args.append(f"    {prop}={example_val},")

            args_str = "\\n".join(args) if args else "    # No required parameters"

            return f"""from servers.{provider} import {func_name}

result = await {func_name}(
{args_str}
)
print(result)"""


        def _get_example_value(schema: dict[str, Any]) -> str:
            """Get example value for a schema type."""
            if "enum" in schema:
                return f'"{schema["enum"][0]}"'

            t = schema.get("type", "string")
            defaults = {
                "string": '"example"',
                "integer": "1",
                "number": "1.0",
                "boolean": "True",
                "array": "[]",
                "object": "{}",
            }
            return defaults.get(t, "None")


        def get_all_interfaces(
            provider: str,
            servers_path: str | Path = DEFAULT_SERVERS_PATH,
        ) -> str:
            """Get Python TypedDict interfaces for all tools in a provider."""
            servers_path = Path(servers_path)
            tools = _load_manifest_tools(provider, servers_path)

            lines = [
                f'"""TypedDict interfaces for {provider} tools."""',
                "",
                "from typing import TypedDict, Any, Optional, List, Literal",
                "",
            ]

            for tool in tools:
                tool_name = tool.get("name", "")
                input_schema = tool.get("inputSchema", {})
                interface = _generate_typed_dict(provider, tool_name, input_schema)
                lines.append(interface)
                lines.append("")

            return "\\n".join(lines)


        def _generate_typed_dict(provider: str, tool_name: str, input_schema: dict[str, Any]) -> str:
            """Generate Python TypedDict class from JSON Schema."""
            class_name = _to_class_name(f"{provider}_{tool_name}_Input")
            properties = input_schema.get("properties", {})
            required = set(input_schema.get("required", []))

            if not properties:
                return f"class {class_name}(TypedDict):\\n    pass"

            lines = [f"class {class_name}(TypedDict):"]
            for prop_name, prop_schema in properties.items():
                prop_type = _json_to_python_type(prop_schema)
                is_required = prop_name in required
                desc = prop_schema.get("description", "")

                if desc:
                    lines.append(f"    # {_truncate(desc, 80)}")
                if is_required:
                    lines.append(f"    {prop_name}: {prop_type}")
                else:
                    lines.append(f"    {prop_name}: Optional[{prop_type}]")

            return "\\n".join(lines)


        def _json_to_python_type(schema: dict[str, Any]) -> str:
            """Convert JSON Schema type to Python type."""
            if not schema:
                return "Any"

            if "enum" in schema:
                literals = ", ".join(f'"{v}"' for v in schema["enum"])
                return f"Literal[{literals}]"

            type_map = {"string": "str", "number": "float", "integer": "int", "boolean": "bool", "null": "None"}
            schema_type = schema.get("type")

            if schema_type in type_map:
                return type_map[schema_type]
            if schema_type == "array":
                item_type = _json_to_python_type(schema.get("items", {}))
                return f"List[{item_type}]"
            if schema_type == "object":
                return "dict[str, Any]"
            if isinstance(schema_type, list):
                return " | ".join(_json_to_python_type({"type": t}) for t in schema_type)

            return "Any"


        def _load_manifest_tools(provider: str, servers_path: Path) -> list[dict[str, Any]]:
            """Load tools from provider manifest."""
            manifest_path = servers_path / provider / "manifest.py"
            if not manifest_path.exists():
                return []

            try:
                spec = importlib.util.spec_from_file_location(f"{provider}.manifest", manifest_path)
                if spec is None or spec.loader is None:
                    return []
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return getattr(module, "TOOLS", [])
            except Exception:
                return []


        def _slugify(value: str) -> str:
            """Convert to valid Python identifier."""
            return re.sub(r"[^0-9a-zA-Z]+", "_", value).strip("_").lower() or "tool"


        def _to_class_name(value: str) -> str:
            """Convert to PascalCase."""
            parts = re.sub(r"[^0-9a-zA-Z]+", " ", value).split()
            return "".join(p.capitalize() for p in parts)


        def _truncate(text: str, max_len: int = 150) -> str:
            """Truncate text."""
            text = " ".join(str(text).split())
            return text if len(text) <= max_len else text[:max_len - 3] + "..."


        # Convenience function for sandbox use
        def discover(query: str = "", limit: int = 20) -> str:
            """Quick discovery helper - returns formatted JSON for sandbox output.

            Usage:
                print(discover("email"))  # Search for email tools
                print(discover())         # List all tools
            """
            if not query:
                providers = list_providers()
                return json.dumps({"providers": providers, "hint": "Use search_tools('query') to find specific tools"}, indent=2)

            results = search_tools(query, limit=limit)
            return json.dumps({
                "tools": results,
                "count": len(results),
                "hint": "Use get_tool_interface(provider, tool_name) for full schema"
            }, indent=2)


        __all__ = [
            "search_tools",
            "list_providers",
            "get_tool_interface",
            "get_all_interfaces",
            "discover",
            "ToolSearchResult",
            "ToolInterface",
        ]
        ''')


def _print_next_steps(provider: str, transport_config: dict[str, Any], provider_dir: Path) -> None:
    env_prefix = _provider_env_prefix(provider)
    init_path = provider_dir / "__init__.py"
    env_path = Path(".env.local")
    transport = transport_config.get("transport", "http")

    print("\nNext steps:")
    print(
        f"  • Export MCP_SERVER_{env_prefix}_TRANSPORT (defaults to '{transport}') plus the"
        " connection-specific variables for secrets."
    )
    if transport == "http":
        print(
            f"    - MCP_SERVER_{env_prefix}_URL (or MCP_SERVER_URL) for the HTTP endpoint;"
            f" use MCP_SERVER_{env_prefix}_HEADERS for API keys."
        )
    else:
        print(
            f"    - MCP_SERVER_{env_prefix}_COMMAND along with optional _ARGS/_CWD/_ENV"
            " to launch the stdio server."
        )
    print(f"  • Non-sensitive defaults already live in {init_path} under SERVER_CONFIG.")
    print(f"  • Secrets passed via CLI are written to {env_path} (edit as needed).\n")


def _write_env_local(provider: str, secret_env: dict[str, str]) -> None:
    if not secret_env:
        return
    env_path = Path(".env.local")
    lines: list[str]
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        new_lines: list[str] = []
    else:
        lines = []
        new_lines = ["# Local MCP secrets managed by mcp_tools CLI", ""]
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" not in line:
            new_lines.append(line)
            continue
        key, _, _ = line.partition("=")
        key = key.strip()
        if key in secret_env:
            new_lines.append(f"{key}={_quote_env_value(secret_env[key])}")
            seen.add(key)
        else:
            new_lines.append(line)
    for key, value in secret_env.items():
        if key not in seen:
            new_lines.append(f"{key}={_quote_env_value(value)}")
    env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    print(f"Stored secrets for {provider} in {env_path}")


def _sync_modal_secret(provider: str, secret_env: dict[str, str]) -> None:
    if not secret_env:
        return
    try:
        import modal
    except Exception as exc:  # pragma: no cover - modal is optional during dev
        print(f"Skipping Modal secret sync (modal import failed: {exc})")
        return

    secret_name = f"mcp-{provider}-secrets"
    try:
        modal.Secret.objects.create(secret_name, secret_env, allow_existing=True)
        print(f"Upserted Modal secret '{secret_name}' with {len(secret_env)} entries.")
    except Exception as exc:  # pragma: no cover - avoid hard failure on CLI tooling
        print(f"Warning: failed to sync Modal secret '{secret_name}': {exc}")


def _render_tool_module(provider: str, provider_title: str, tool_data: dict[str, Any]) -> str:
    tool_name = tool_data.get("name", "tool")
    module_title = provider_title or provider
    function_name = _slugify(tool_name)
    body = _format_tool_definition(tool_data)
    docstring = _collapse_description(tool_data.get("description") or tool_name)
    provider_literal = json.dumps(provider)
    lines = [
        f'"""Auto-generated wrapper for {module_title} → {tool_name}."""',
        "",
        "from __future__ import annotations",
        "",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "try:",
        "    from servers._runtime import call_tool",
        "except ImportError:  # Modal uploads omit the 'servers' package",
        "    import sys",
        "    root = Path(__file__).resolve().parent.parent",
        "    root_str = str(root)",
        "    if root_str not in sys.path:",
        "        sys.path.append(root_str)",
        "    from _runtime import call_tool",
        "",
        f"TOOL = {body}",
        "",
        f"async def {function_name}(*args: Any, **kwargs: Any) -> Any:",
    ]
    if docstring:
        lines.append(f'    """{docstring}"""')
    else:
        lines.append('    """Invoke the tool via call_tool."""')
    lines.append(f"    return await call_tool({provider_literal}, TOOL, *args, **kwargs)")
    lines.append("")
    lines.append(f"__all__ = ('TOOL', '{function_name}')")
    lines.append("")
    return "\n".join(lines)


def _render_provider_init(
    provider: str,
    provider_title: str,
    modules: list[str],
    transport_config: dict[str, Any],
) -> str:
    """Render the provider's __init__.py with direct function re-exports.

    This allows users to do:
        from servers.gmail import gmail_send_email
    Instead of:
        from servers.gmail.gmail_send_email import gmail_send_email
    """
    module_title = provider_title or provider
    lines = [
        f'"""Auto-generated tool package for {module_title}.',
        "",
        "Usage:",
        f"    from servers.{provider} import <tool_function>",
        "",
        "Example:",
        f"    from servers.{provider} import {modules[0] if modules else 'tool_name'}",
        f"    result = await {modules[0] if modules else 'tool_name'}(param=value)",
        '"""',
        "",
        "from __future__ import annotations",
        "",
    ]

    # Import modules (for backward compatibility)
    for module in modules:
        lines.append(f"from . import {module} as _{module}_module")

    # Re-export the actual functions directly
    lines.append("")
    lines.append("# Re-export tool functions for convenient imports")
    for module in modules:
        lines.append(f"from .{module} import {module}")

    lines.append("from . import manifest")
    lines.append("")
    lines.append("# Non-sensitive defaults for this provider.")
    lines.append(f"SERVER_CONFIG = {_format_tool_definition(transport_config)}")
    lines.append("")

    # __all__ includes functions directly
    all_names = [f'"{name}"' for name in modules]
    all_names.extend(['"manifest"', '"SERVER_CONFIG"'])
    joined = ", ".join(all_names)
    lines.append(f"__all__ = ({joined},)")
    lines.append("")
    return "\n".join(lines)


def _write_manifest(provider_dir: Path, provider: str, tool_entries: list[dict[str, Any]]) -> None:
    manifest_path = provider_dir / "manifest.py"
    manifest_path.write_text(_render_manifest(provider, tool_entries), encoding="utf-8")


def _write_interfaces(
    provider_dir: Path, provider: str, tool_entries: list[dict[str, Any]]
) -> None:
    """Write TypedDict interfaces for all tools in the provider.

    This enables LLMs to understand exact parameter types and provides
    IDE-friendly type hints for tool usage.
    """
    interfaces_path = provider_dir / "interfaces.py"
    interfaces_path.write_text(_render_interfaces(provider, tool_entries), encoding="utf-8")


def _render_interfaces(provider: str, tool_entries: list[dict[str, Any]]) -> str:
    """Generate Python TypedDict interfaces for all tools."""
    lines = [
        f'"""Auto-generated TypedDict interfaces for {provider} MCP tools.',
        "",
        "These interfaces provide type hints for tool parameters.",
        "Import and use these for IDE autocompletion and type checking.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, List, Optional, TypedDict, Literal",
        "",
    ]

    for tool in tool_entries:
        tool_name = tool.get("name", "unknown")
        description = tool.get("description", "")
        input_schema = tool.get("inputSchema", {})

        class_name = _to_class_name(f"{provider}_{tool_name}_Input")
        interface = _json_schema_to_typed_dict(class_name, input_schema, description)
        lines.append(interface)
        lines.append("")

    # Add __all__ export
    class_names = [
        f'"{_to_class_name(f"{provider}_{t.get('name', 'unknown')}_Input")}"' for t in tool_entries
    ]
    lines.append(f"__all__ = ({', '.join(class_names)},)")
    lines.append("")

    return "\n".join(lines)


def _json_schema_to_typed_dict(
    class_name: str, schema: dict[str, Any], description: str = ""
) -> str:
    """Convert JSON Schema to Python TypedDict class definition."""
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    lines = []
    if description:
        collapsed = _collapse_description(description)
        lines.append(f"# {collapsed}")

    lines.append(f"class {class_name}(TypedDict):")

    if not properties:
        lines.append("    pass  # No parameters required")
        return "\n".join(lines)

    for prop_name, prop_schema in properties.items():
        prop_type = _json_type_to_python(prop_schema)
        prop_desc = prop_schema.get("description", "")
        is_required = prop_name in required

        if prop_desc:
            lines.append(f"    # {_collapse_description(prop_desc)[:80]}")

        if is_required:
            lines.append(f"    {prop_name}: {prop_type}")
        else:
            lines.append(f"    {prop_name}: Optional[{prop_type}]")

    return "\n".join(lines)


def _json_type_to_python(schema: dict[str, Any]) -> str:
    """Convert JSON Schema type to Python type annotation."""
    if not schema:
        return "Any"

    schema_type = schema.get("type")

    if "enum" in schema:
        literals = ", ".join(f'"{v}"' for v in schema["enum"])
        return f"Literal[{literals}]"

    type_mapping = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "null": "None",
    }

    if schema_type in type_mapping:
        return type_mapping[schema_type]

    if schema_type == "array":
        items = schema.get("items", {})
        item_type = _json_type_to_python(items)
        return f"List[{item_type}]"

    if schema_type == "object":
        additional = schema.get("additionalProperties")
        if additional:
            value_type = _json_type_to_python(additional)
            return f"dict[str, {value_type}]"
        return "dict[str, Any]"

    if isinstance(schema_type, list):
        types = [_json_type_to_python({"type": t}) for t in schema_type]
        return " | ".join(types)

    return "Any"


def _to_class_name(value: str) -> str:
    """Convert string to PascalCase class name."""
    parts = re.sub(r"[^0-9a-zA-Z]+", " ", value).split()
    return "".join(part.capitalize() for part in parts)


def _render_manifest(provider: str, tool_entries: list[dict[str, Any]]) -> str:
    manifest_literal = _format_tool_definition(tool_entries)
    return textwrap.dedent(
        f'''"""Tool manifest for {provider}.

Provides lightweight search + schema lookup so sandboxes can discover tools without
loading every wrapper module.
"""

from __future__ import annotations

from typing import Any, List

TOOLS: List[dict[str, Any]] = {manifest_literal}


def search_tools(query: str) -> List[dict[str, Any]]:
    """Return tools whose name or description contains the query (case-insensitive)."""

    normalized = (query or "").strip().lower()
    if not normalized:
        return list(TOOLS)
    results: list[dict[str, Any]] = []
    for tool in TOOLS:
        name = str(tool.get("name", "")).lower()
        description = str(tool.get("description", "")).lower()
        if normalized in name or normalized in description:
            results.append(tool)
    return results


__all__ = ("TOOLS", "search_tools")
'''
    )


def _format_tool_definition(tool_data: dict[str, Any]) -> str:
    ordered = _order_data(tool_data)
    return repr(ordered)


def _write_runtime_module(base_dir: Path) -> None:
    runtime_path = base_dir / RUNTIME_MODULE_NAME
    content = _render_runtime_module()
    if runtime_path.exists():
        existing = runtime_path.read_text(encoding="utf-8")
        if existing == content:
            return
    runtime_path.write_text(content, encoding="utf-8")


def _render_runtime_module() -> str:
    return textwrap.dedent(
        '''\
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
        '''
    )


def _slugify(value: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z]+", "_", value).strip("_").lower()
    return value or "tool"


def _collapse_description(value: str | None) -> str:
    if not value:
        return ""
    collapsed = " ".join(value.split())
    return collapsed.replace('"""', '\\"""')


def _provider_env_prefix(provider: str) -> str:
    normalized = re.sub(r"[^0-9A-Z]+", "_", provider.upper()).strip("_")
    return normalized or "DEFAULT"


def _quote_env_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _order_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _order_data(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_order_data(item) for item in value]
    return value


def _parse_key_values(entries: list[str], flag_name: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"{flag_name} values must use KEY=VALUE format (got '{entry}')")
        key, value = entry.split("=", 1)
        parsed[key] = value
    return parsed


def main() -> None:
    args = parse_args()
    tools, server_name, transport_config, secret_env = asyncio.run(fetch_tools(args))
    provider_dir, tool_count = sync_to_disk(
        args.provider,
        server_name,
        tools,
        args.output_dir,
        transport_config,
    )
    print(f"Wrote {tool_count} tools to {provider_dir}")
    print("  - manifest.py: Tool search index")
    print("  - interfaces.py: TypedDict definitions for LLM context")
    _write_env_local(args.provider, secret_env)
    _sync_modal_secret(args.provider, secret_env)
    _print_next_steps(args.provider, transport_config, provider_dir)
    if args.modal_upload:
        maybe_upload_to_modal(args.output_dir.resolve(), provider_dir, args.provider)
        print("Uploaded to Modal volume:")
        print(f"  - /{args.provider}/ (provider tools)")
        print("  - /_runtime.py (MCP call runtime)")
        print("  - /_code_mode.py (progressive discovery helpers)")


if __name__ == "__main__":
    main()
