"""
Dynamic tool registry.

Tool contract — every module in tools/core/ and tools/generated/ must expose:
    NAME: str
    DESCRIPTION: str
    INPUT_SCHEMA: dict   (JSON Schema)
    OUTPUT_SCHEMA: dict  (JSON Schema)
    def execute(**kwargs) -> dict: ...
"""
from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, Callable

_CORE_DIR = Path(__file__).parent / "core"
_GEN_DIR  = Path(__file__).parent / "generated"

# SQL DML/DDL keywords matched with word boundaries (case-insensitive) so that
# legitimate Python identifiers like `execute` or `update_result` are not blocked.
_FORBIDDEN_SQL_RE = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|EXEC|ALTER|TRUNCATE)\b",
    re.IGNORECASE,
)
# Python-specific dangerous patterns checked as exact substrings.
_FORBIDDEN_CODE = [
    "os.system", "subprocess", "eval(", "exec(", "__import__",
]


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        output_schema: dict,
        execute: Callable,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.execute = execute

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._load_directory(_CORE_DIR, "tools.core")
        _GEN_DIR.mkdir(parents=True, exist_ok=True)
        self._load_directory(_GEN_DIR, "tools.generated")

    def _load_directory(self, directory: Path, prefix: str) -> None:
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            module_name = f"{prefix}.{path.stem}"
            try:
                if module_name in sys.modules:
                    mod = importlib.reload(sys.modules[module_name])
                else:
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)
                self._register_module(mod)
            except Exception as exc:
                print(f"[ToolRegistry] Warning: skipped {path.name}: {exc}")

    def _register_module(self, mod) -> None:
        required = ["NAME", "DESCRIPTION", "INPUT_SCHEMA", "OUTPUT_SCHEMA", "execute"]
        if not all(hasattr(mod, attr) for attr in required):
            return
        self._tools[mod.NAME] = Tool(
            name=mod.NAME,
            description=mod.DESCRIPTION,
            input_schema=mod.INPUT_SCHEMA,
            output_schema=mod.OUTPUT_SCHEMA,
            execute=mod.execute,
        )

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [t.to_dict() for t in self._tools.values()]

    def register_tool(self, name: str, code: str, description: str = "") -> bool:
        """
        Denylist-scan code, write to tools/generated/<name>.py, and hot-load.
        Returns True on success.
        """
        m = _FORBIDDEN_SQL_RE.search(code)
        if m:
            print(f"[ToolRegistry] Rejected '{name}': contains forbidden SQL keyword '{m.group()}'")
            return False
        for term in _FORBIDDEN_CODE:
            if term in code:
                print(f"[ToolRegistry] Rejected '{name}': contains '{term}'")
                return False

        dest = _GEN_DIR / f"{name}.py"
        dest.write_text(code, encoding="utf-8")
        try:
            module_name = f"tools.generated.{name}"
            sys.modules.pop(module_name, None)
            spec = importlib.util.spec_from_file_location(module_name, dest)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
            self._register_module(mod)
            print(f"[ToolRegistry] Registered: {name}")
            return True
        except Exception as exc:
            print(f"[ToolRegistry] Load failed for '{name}': {exc}")
            dest.unlink(missing_ok=True)
            return False


# Global singleton
registry = ToolRegistry()
