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

            args_str = "\n".join(args) if args else "    # No required parameters"

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

            return "\n".join(lines)


        def _generate_typed_dict(provider: str, tool_name: str, input_schema: dict[str, Any]) -> str:
            """Generate Python TypedDict class from JSON Schema."""
            class_name = _to_class_name(f"{provider}_{tool_name}_Input")
            properties = input_schema.get("properties", {})
            required = set(input_schema.get("required", []))

            if not properties:
                return f"class {class_name}(TypedDict):\n    pass"

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

            return "\n".join(lines)


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
