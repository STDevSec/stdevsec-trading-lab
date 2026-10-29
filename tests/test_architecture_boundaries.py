"""Cross-cutting architecture tests.

Enforces the dependency rule from ADR-0002: the quant-engine must stay
independent of the web/application stack so it remains reproducible and usable
standalone.
"""

from __future__ import annotations

import ast
from pathlib import Path

QUANT_ENGINE_SRC = (
    Path(__file__).resolve().parent.parent / "packages" / "quant-engine" / "src" / "quant_engine"
)

FORBIDDEN_IMPORTS = {"fastapi", "starlette", "sqlalchemy", "redis", "uvicorn", "stdevsec_api"}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    return mods


def test_quant_engine_has_no_app_dependencies() -> None:
    offenders: dict[str, set[str]] = {}
    for py in QUANT_ENGINE_SRC.rglob("*.py"):
        bad = _imported_modules(py) & FORBIDDEN_IMPORTS
        if bad:
            offenders[str(py)] = bad
    assert not offenders, f"quant-engine imports app-layer modules: {offenders}"
