from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_DOCS_DEPENDENCIES = {
    "mkdocs>=1.6.1,<2",
    "mkdocs-material>=9.7.6,<10",
    "mkdocs-minify-plugin>=0.8,<1",
}
LOCKED_SYNC = "uv sync --project backend --locked --only-group docs"
LOCKED_RUN = "uv run --project backend --no-sync"


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_docs_dependency_group_is_declared_and_locked() -> None:
    pyproject = tomllib.loads(_read("backend/pyproject.toml"))
    docs_dependencies = set(pyproject["dependency-groups"]["docs"])

    assert docs_dependencies == EXPECTED_DOCS_DEPENDENCIES

    lockfile = _read("backend/uv.lock")
    for package_name in ("mkdocs", "mkdocs-material", "mkdocs-minify-plugin"):
        assert f'name = "{package_name}"' in lockfile


def test_docs_ci_builds_strictly_from_the_locked_docs_group() -> None:
    workflow_text = _read(".github/workflows/docs-ci.yml")
    workflow = " ".join(workflow_text.split())

    assert workflow_text.count('      - "backend/uv.lock"') == 2
    assert 'UV_VERSION: "0.11.23"' in workflow
    assert 'UV_PROJECT_ENVIRONMENT: ".venv-docs"' in workflow
    assert 'python-version: "3.12"' in workflow
    assert 'python -m pip install "uv==${UV_VERSION}"' in workflow
    assert LOCKED_SYNC in workflow
    assert f"{LOCKED_RUN} mkdocs build --strict --config-file mkdocs.yml" in workflow


def test_docs_deploy_uses_the_same_locked_toolchain() -> None:
    workflow_text = _read(".github/workflows/deploy-docs.yml")
    workflow = " ".join(workflow_text.split())

    assert '      - "backend/pyproject.toml"' in workflow_text
    assert '      - "backend/uv.lock"' in workflow_text
    assert 'UV_VERSION: "0.11.23"' in workflow
    assert 'UV_PROJECT_ENVIRONMENT: ".venv-docs"' in workflow
    assert 'python-version: "3.12"' in workflow
    assert 'python -m pip install "uv==${UV_VERSION}"' in workflow
    assert LOCKED_SYNC in workflow
    assert f"{LOCKED_RUN} mkdocs gh-deploy --strict --force --config-file mkdocs.yml" in workflow
    assert 'pip install "mkdocs<2"' not in workflow_text


def test_make_target_preserves_the_backend_environment() -> None:
    makefile = _read("Makefile")
    backend_ignore = _read("backend/.gitignore")

    assert "docs-build:" in makefile
    assert (
        "UV_PROJECT_ENVIRONMENT=.venv-docs "
        "uv sync --project backend --locked --only-group docs" in makefile
    )
    assert (
        "UV_PROJECT_ENVIRONMENT=.venv-docs "
        "uv run --project backend --no-sync mkdocs build --strict "
        "--config-file mkdocs.yml" in makefile
    )
    assert ".venv-docs/" in backend_ignore.splitlines()
