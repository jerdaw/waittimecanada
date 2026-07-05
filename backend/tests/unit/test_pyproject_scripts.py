"""Packaging metadata tests."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


def test_project_scripts_resolve_to_importable_callables() -> None:
    """Console script metadata should not point to missing modules."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    scripts = pyproject["project"].get("scripts", {})

    assert scripts, "expected backend console scripts to be declared"
    for script_name, entrypoint in scripts.items():
        module_name, function_name = entrypoint.split(":", maxsplit=1)
        module = importlib.import_module(module_name)
        target = getattr(module, function_name)

        assert callable(target), f"{script_name} target {entrypoint} is not callable"
