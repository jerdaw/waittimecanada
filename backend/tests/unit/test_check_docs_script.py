import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


DOCS_CI_PATTERNS = [
    "**/*.md",
    "**/*.txt",
    "**/*.rst",
    "**/*.py",
    "**/*.ts",
    "**/*.tsx",
    "**/*.js",
    "**/*.jsx",
    "**/*.json",
    "**/*.yml",
    "**/*.yaml",
    "**/*.sh",
    "**/*.sql",
    "**/*.css",
    "**/*.html",
    "**/*.csv",
    "**/*.toml",
    "**/*.ini",
    "**/*.cfg",
    "docs/**",
]


ENUMS_PY = """\
from enum import StrEnum


class MetricFamily(StrEnum):
    TIME_TO_PROVIDER = "TIME_TO_PROVIDER"
    TOTAL_LOS = "TOTAL_LOS"
    STRETCHER_OCCUPANCY = "STRETCHER_OCCUPANCY"


class StartEvent(StrEnum):
    TRIAGE = "TRIAGE"
    REGISTRATION = "REGISTRATION"
    DOOR = "DOOR"
    UNKNOWN = "UNKNOWN"


class EndEvent(StrEnum):
    PHYSICIAN = "PHYSICIAN"
    PROVIDER = "PROVIDER"
    DISCHARGE = "DISCHARGE"
    FIRST_ASSESSMENT = "FIRST_ASSESSMENT"


class StatisticType(StrEnum):
    P90 = "P90"
    MEDIAN = "MEDIAN"
    MEAN = "MEAN"
    ROLLING_AVG = "ROLLING_AVG"
    ALGORITHMIC = "ALGORITHMIC"
    POINT_ESTIMATE = "POINT_ESTIMATE"


class PatientScope(StrEnum):
    ALL = "ALL"
    MID_ACUITY = "MID_ACUITY"
    NON_PRIORITY = "NON_PRIORITY"
    HIGH_ACUITY = "HIGH_ACUITY"
"""


AGENTS_MD = """\
# AGENTS.md

```python
METRIC_FAMILY = ["TIME_TO_PROVIDER", "TOTAL_LOS", "STRETCHER_OCCUPANCY"]
START_EVENT = ["TRIAGE", "REGISTRATION", "DOOR", "UNKNOWN"]
END_EVENT = ["PHYSICIAN", "PROVIDER", "DISCHARGE", "FIRST_ASSESSMENT"]
STATISTIC_TYPE = ["P90", "MEDIAN", "MEAN", "ROLLING_AVG", "ALGORITHMIC", "POINT_ESTIMATE"]
PATIENT_SCOPE = ["ALL", "MID_ACUITY", "NON_PRIORITY", "HIGH_ACUITY"]
```
"""


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _required_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required to run this test")
    return executable


def _docs_ci_yaml() -> str:
    pattern_lines = "\n".join(f'      - "{pattern}"' for pattern in DOCS_CI_PATTERNS)
    return f"""\
name: Docs CI

on:
  pull_request:
    paths:
{pattern_lines}
  push:
    branches: [main]
    paths:
{pattern_lines}
  workflow_dispatch:

jobs:
  docs-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - name: Run docs quality checks
        run: bash scripts/check-docs.sh
"""


def _create_docs_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()

    _write(
        root / "scripts" / "check-docs.sh",
        (REPO_ROOT / "scripts" / "check-docs.sh").read_text(encoding="utf-8"),
    )
    _write(
        root / "README.md",
        "does not provide medical advice\nCall 911 for emergencies\ndirectly comparable\n",
    )
    _write(root / "CONTRIBUTING.md")
    _write(root / "AGENTS.md", AGENTS_MD)
    _write(root / "CHANGELOG.md")
    _write(root / "SECURITY.md")
    _write(root / "backend" / "README.md")
    _write(root / "backend" / "migrations" / "README.md")
    _write(root / "backend" / "src" / "waittime" / "core" / "enums.py", ENUMS_PY)
    _write(
        root / "backend" / "scripts" / "verify_roadmap_consistency.py",
        "print('roadmap consistency stub passed')\n",
    )
    _write(root / "frontend" / "README.md")
    _write(root / ".github" / "workflows" / "docs-ci.yml", _docs_ci_yaml())
    _write(root / ".github" / "workflows" / "README.md")

    _write(root / "docs" / "README.md")
    _write(
        root / "docs" / "API.md",
        "not a triage or medical advice service\nontology dimensions match\n",
    )
    _write(
        root / "docs" / "case-studies" / "ottawa-gatineau-divergence.md",
        "not directly comparable\n",
    )
    _write(
        root / "docs" / "research" / "export-methodology-interpretation-guide.md",
        "medical advice, triage guidance, or care-site\n"
        "metric_family\n"
        "start_event\n"
        "end_event\n"
        "statistic_type\n",
    )
    _write(
        root / "docs" / "planning" / "roadmap.md",
        "hospital-choice recommendations\n"
        "metric family, start event, end event, and statistic type\n",
    )
    _write(root / "docs" / "stakeholder-interviews" / "README.md", "[ok]: ../README.md\n")

    os.symlink("AGENTS.md", root / "CLAUDE.md")
    os.symlink("AGENTS.md", root / "GEMINI.md")

    git = _required_executable("git")
    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        [git, "init"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        [git, "config", "user.name", "Jeremy Dawson"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        [git, "config", "user.email", "jeremyjdawson@gmail.com"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        [git, "config", "commit.gpgsign", "false"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        [git, "add", "."],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    _git_commit(root, "Initial fixture", author="Jeremy Dawson <jeremyjdawson@gmail.com>")
    return root


def _git_add(root: Path, path: str) -> None:
    git = _required_executable("git")
    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        [git, "add", path],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _git_commit(root: Path, *messages: str, author: str | None = None) -> None:
    git = _required_executable("git")
    command = [git, "commit"]
    if author is not None:
        command.extend(["--author", author])
    for message in messages:
        command.extend(["-m", message])

    subprocess.run(  # noqa: S603 - trusted fixture repo and resolved git path.
        command,
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_check_docs(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - trusted fixture script and resolved bash path.
        [_required_executable("bash"), "scripts/check-docs.sh"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_check_docs_fixture_passes(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)

    result = _run_check_docs(root)

    assert result.returncode == 0, result.stdout + result.stderr


def test_check_docs_rejects_agents_ontology_drift(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    agents_path = root / "AGENTS.md"
    agents_path.write_text(
        AGENTS_MD.replace(', "HIGH_ACUITY"', ""),
        encoding="utf-8",
    )

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "AGENTS.md ontology constants are out of sync" in result.stdout


def test_check_docs_rejects_reference_style_broken_link(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    stakeholder_readme = root / "docs" / "stakeholder-interviews" / "README.md"
    stakeholder_readme.write_text("[missing]: missing.md\n", encoding="utf-8")

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "Broken link target" in result.stdout
    assert "missing.md" in result.stdout


def test_check_docs_requires_broad_docs_path_filter(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    workflow_path = root / ".github" / "workflows" / "docs-ci.yml"
    workflow_path.write_text(
        workflow_path.read_text(encoding="utf-8").replace('      - "docs/**"\n', ""),
        encoding="utf-8",
    )

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert 'Docs CI pull_request path filters must include "docs/**"' in result.stdout
    assert 'Docs CI push path filters must include "docs/**"' in result.stdout


def test_check_docs_requires_full_history_for_commit_audit(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    workflow_path = root / ".github" / "workflows" / "docs-ci.yml"
    workflow_path.write_text(
        workflow_path.read_text(encoding="utf-8").replace(
            "        with:\n          fetch-depth: 0\n",
            "",
        ),
        encoding="utf-8",
    )

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "Docs CI checkout must use fetch-depth: 0" in result.stdout


def test_check_docs_rejects_file_url_in_public_csv(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    _write(
        root / "docs" / "assets" / "methodology.csv",
        "source,path\nexample,file:///tmp/private.csv\n",
    )

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "methodology.csv" in result.stdout
    assert "file:///tmp/private.csv" in result.stdout


def test_check_docs_requires_agent_entrypoint_symlink(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    claude_path = root / "CLAUDE.md"
    claude_path.unlink()
    claude_path.write_text("AGENTS.md\n", encoding="utf-8")

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "CLAUDE.md must remain a relative symlink to AGENTS.md" in result.stdout


def test_check_docs_rejects_local_home_path_not_url_route(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    research_doc = root / "docs" / "research" / "local-path-check.md"
    research_doc.write_text(
        "Allowed URL: https://example.test/home/item\n"
        "Leaked local path: /home/alice/waittimecanada\n",
        encoding="utf-8",
    )

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "local-path-check.md" in result.stdout
    assert "/home/alice/waittimecanada" in result.stdout


def test_check_docs_rejects_non_human_attribution_in_new_public_doc(
    tmp_path: Path,
) -> None:
    root = _create_docs_fixture(tmp_path)
    attribution_doc = root / "docs" / "research" / "attribution.md"
    attribution_doc.write_text("Author: ChatGPT\n", encoding="utf-8")

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "attribution.md" in result.stdout
    assert "Author: ChatGPT" in result.stdout


def test_check_docs_rejects_non_human_attribution_in_tracked_source(
    tmp_path: Path,
) -> None:
    root = _create_docs_fixture(tmp_path)
    source_file = root / "frontend" / "utils" / "generated.ts"
    marker = "Generated by " + "ChatGPT"
    _write(source_file, f"// {marker}\n")
    _git_add(root, "frontend/utils/generated.ts")

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "generated.ts" in result.stdout
    assert marker in result.stdout


def test_check_docs_rejects_non_human_commit_author(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    source_file = root / "docs" / "research" / "commit-author.md"
    _write(source_file, "Commit metadata fixture\n")
    _git_add(root, "docs/research/commit-author.md")
    _git_commit(root, "Commit metadata fixture", author="Codex <codex@example.invalid>")

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "Git history contains non-human author/committer metadata" in result.stdout


def test_check_docs_rejects_non_human_commit_trailer(tmp_path: Path) -> None:
    root = _create_docs_fixture(tmp_path)
    source_file = root / "docs" / "research" / "commit-trailer.md"
    _write(source_file, "Commit trailer fixture\n")
    _git_add(root, "docs/research/commit-trailer.md")
    _git_commit(
        root,
        "Commit trailer fixture",
        "Co-authored-by: ChatGPT <chatgpt@example.invalid>",
        author="Jeremy Dawson <jeremyjdawson@gmail.com>",
    )

    result = _run_check_docs(root)

    assert result.returncode == 1
    assert "Git history contains non-human authorship or attribution trailers" in result.stdout
