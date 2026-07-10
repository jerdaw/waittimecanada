# Reproducible MkDocs Toolchain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make strict MkDocs validation reproducible through the checked-in uv lock while keeping documentation tooling isolated from the backend development environment.

**Architecture:** A `docs` dependency group in `backend/pyproject.toml` and `backend/uv.lock` owns the complete toolchain. Local commands, Docs CI, and the GitHub Pages workflow select that group through a separate `.venv-docs` environment; workflow-contract tests prevent floating installs or validation/deployment drift.

**Tech Stack:** Python 3.12, uv 0.11.23, MkDocs 1.6.x, Material for MkDocs 9.7.x, mkdocs-minify-plugin 0.8.x, pytest, GitHub Actions, GNU Make.

**Status:** In progress. Task 1 is complete: the four contract tests pass,
`uv lock --check` passes, both workflow files parse as YAML, and manual Docs CI
run `29096472950` passed the locked sync plus strict MkDocs build on commit
`5c4bf1d6a32c618e25b589681e3a513eb9a06072` without invoking deployment.

## Global Constraints

- Never inspect or print `.env*`, credentials, keys, certificates, or private maintainer notes.
- Keep MkDocs constrained to `>=1.6.1,<2` until the separately documented migration gate opens.
- Keep Material for MkDocs constrained to `>=9.7.6,<10` and mkdocs-minify-plugin to `>=0.8,<1`.
- Use `UV_PROJECT_ENVIRONMENT=.venv-docs`; do not replace or prune `backend/.venv`.
- Use `uv sync --project backend --locked --only-group docs` for exact environment setup.
- Run MkDocs from the repository root with `--project backend`, `--no-sync`, and `--config-file mkdocs.yml`.
- Preserve the current `mkdocs gh-deploy --force` publication mechanism and GitHub Pages permissions.
- Do not dispatch, merge, deploy, release, publish, modify secrets, or exercise the deployment command during implementation.
- Stop at a reviewed, green, ready pull request because merging changed `docs/**` paths triggers the existing deployment workflow.

---

### Task 1: Locked Documentation Toolchain And Workflow Contract

**Files:**
- Create: `backend/tests/unit/test_docs_toolchain.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `backend/.gitignore`
- Modify: `.github/workflows/docs-ci.yml`
- Modify: `.github/workflows/deploy-docs.yml`
- Modify: `Makefile`

**Interfaces:**
- Consumes: uv project metadata in `backend/pyproject.toml`, `mkdocs.yml`, and the existing GitHub Actions checkout/authentication steps.
- Produces: dependency group `docs`; generated environment `backend/.venv-docs`; Make target `docs-build`; locked workflow commands shared by validation and deployment.

- [x] **Step 1: Add failing workflow and dependency contract tests**

Create `backend/tests/unit/test_docs_toolchain.py`:

```python
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
    assert (
        f"{LOCKED_RUN} mkdocs build --strict --config-file mkdocs.yml"
        in workflow
    )


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
    assert (
        f"{LOCKED_RUN} mkdocs gh-deploy --strict --force "
        "--config-file mkdocs.yml"
        in workflow
    )
    assert 'pip install "mkdocs<2"' not in workflow_text


def test_make_target_preserves_the_backend_environment() -> None:
    makefile = _read("Makefile")
    backend_ignore = _read("backend/.gitignore")

    assert "docs-build:" in makefile
    assert (
        "UV_PROJECT_ENVIRONMENT=.venv-docs "
        "uv sync --project backend --locked --only-group docs"
        in makefile
    )
    assert (
        "UV_PROJECT_ENVIRONMENT=.venv-docs "
        "uv run --project backend --no-sync mkdocs build --strict "
        "--config-file mkdocs.yml"
        in makefile
    )
    assert ".venv-docs/" in backend_ignore.splitlines()
```

- [x] **Step 2: Run the tests and verify the current contract fails**

Run:

```bash
cd backend
TMPDIR=/tmp TMP=/tmp TEMP=/tmp .venv/bin/python -m pytest \
  tests/unit/test_docs_toolchain.py -v
```

Expected: four tests fail because the dependency group, lock entries, workflow commands, Make target, and ignore entry do not exist.

- [x] **Step 3: Declare the docs dependency group and isolated environment**

Append to `backend/pyproject.toml` after the optional dependencies:

```toml
[dependency-groups]
docs = [
    "mkdocs>=1.6.1,<2",
    "mkdocs-material>=9.7.6,<10",
    "mkdocs-minify-plugin>=0.8,<1",
]
```

Add to `backend/.gitignore` beside `.venv/`:

```gitignore
.venv-docs/
```

Regenerate and check the lock:

```bash
cd backend
python -m pip install "uv==0.11.23"
uv lock
uv lock --check
```

Expected: `backend/uv.lock` contains the three direct documentation packages and their resolved transitive dependencies; `uv lock --check` exits 0.

- [x] **Step 4: Add the local strict-build target**

Append to `Makefile`:

```make
.PHONY: docs-build
docs-build: ## Install the locked docs toolchain separately and run a strict site build
	UV_PROJECT_ENVIRONMENT=.venv-docs uv sync --project backend --locked --only-group docs
	UV_PROJECT_ENVIRONMENT=.venv-docs uv run --project backend --no-sync mkdocs build --strict --config-file mkdocs.yml
```

- [x] **Step 5: Make Docs CI install and exercise the locked toolchain**

Add `backend/uv.lock` to both path-filter lists in `.github/workflows/docs-ci.yml`, then add the workflow environment:

```yaml
env:
  UV_VERSION: "0.11.23"
  UV_PROJECT_ENVIRONMENT: ".venv-docs"
```

After checkout, retain the existing docs-quality step and append:

```yaml
      - name: Set up Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405
        with:
          python-version: "3.12"
      - name: Install locked documentation dependencies
        run: |
          python -m pip install "uv==${UV_VERSION}"
          uv sync --project backend --locked --only-group docs
      - name: Build documentation in strict mode
        run: >-
          uv run --project backend --no-sync mkdocs build --strict
          --config-file mkdocs.yml
```

- [x] **Step 6: Make deployment use the identical locked environment**

Add `backend/pyproject.toml` and `backend/uv.lock` to the push paths in `.github/workflows/deploy-docs.yml`. Add the same workflow environment used by Docs CI:

```yaml
env:
  UV_VERSION: "0.11.23"
  UV_PROJECT_ENVIRONMENT: ".venv-docs"
```

Set the existing Python action to `python-version: "3.12"`. Replace the install and deploy steps with:

```yaml
      - name: Install locked documentation dependencies
        run: |
          python -m pip install "uv==${UV_VERSION}"
          uv sync --project backend --locked --only-group docs

      - name: Build and Deploy
        run: >-
          uv run --project backend --no-sync mkdocs gh-deploy --strict --force
          --config-file mkdocs.yml
```

Do not run or dispatch the deploy workflow during implementation.

- [x] **Step 7: Run focused red/green and toolchain validation**

Run:

```bash
cd backend
TMPDIR=/tmp TMP=/tmp TEMP=/tmp .venv/bin/python -m pytest \
  tests/unit/test_docs_toolchain.py -v
uv lock --check
cd ..
UV_PROJECT_ENVIRONMENT=.venv-docs uv sync \
  --project backend --locked --only-group docs
UV_PROJECT_ENVIRONMENT=.venv-docs uv run \
  --project backend --no-sync mkdocs build --strict --config-file mkdocs.yml
git diff --check
```

Expected: four focused tests pass; the lock check, isolated sync, strict build, and whitespace check exit 0. No deployment command is invoked.

- [x] **Step 8: Commit the locked tooling contract**

```bash
git add backend/tests/unit/test_docs_toolchain.py backend/pyproject.toml \
  backend/uv.lock backend/.gitignore .github/workflows/docs-ci.yml \
  .github/workflows/deploy-docs.yml Makefile
git commit -m "build: lock MkDocs validation toolchain"
```

### Task 2: Contributor Guidance And Completion Evidence

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/development/documentation-guidelines.md`
- Modify: `docs/maintenance-audit.md`
- Modify: `docs/planning/roadmap.md`
- Modify: `docs/planning/README.md`
- Modify: `docs/superpowers/plans/2026-07-10-reproducible-mkdocs-toolchain.md`

**Interfaces:**
- Consumes: `make docs-build` and the locked workflow contract delivered by Task 1.
- Produces: one documented contributor command, durable completion evidence, and removal of the finished maintenance item from active selection.

- [x] **Step 1: Document the supported contributor command**

In `CONTRIBUTING.md`, add the strict documentation build after `bash scripts/check-docs.sh`:

```markdown
# Install the locked docs-only environment and build the site strictly
make docs-build
```

In `docs/development/documentation-guidelines.md`, replace the single-command quality section with:

````markdown
Run both documentation gates before opening a docs-heavy PR:

```bash
bash scripts/check-docs.sh
make docs-build
```

`make docs-build` uses the locked `docs` dependency group in
`backend/uv.lock` and keeps it in `backend/.venv-docs`, separate from the
backend development environment.
````

- [x] **Step 2: Close the maintenance and roadmap item**

Apply these exact status changes in `docs/maintenance-audit.md`:

```markdown
| `make docs-build` (`mkdocs build --strict`) | Passed | Locked docs-only uv environment; strict site build completed without warnings. |
```

Add `strict MkDocs site build` to the Docs/tooling baseline bullet, remove the
known-lane sentence that says the docs toolchain still needs installation, and
replace the release-readiness row with:

```markdown
| Docs site strict build | Ready for local verification | `make docs-build` passed with the locked docs-only environment. |
```

Remove the unavailable MkDocs bullet from `Failed or unavailable`. Replace
`Remaining Recommendations` with:

```markdown
1. Run the disposable database verification helper before a release when
   database-backed integration, migrations-on-fresh-DB, pipeline smoke, and
   Playwright coverage are required.
2. Consider a focused backend service maintainability pass for the largest
   database service surfaces.
3. Keep dependency upgrades separate unless required by security, compatibility,
   or owner-directed maintenance.
```

Remove the risk sentence that says `mkdocs build --strict` remains unavailable.

In `docs/planning/roadmap.md`, append this sentence to the current maintenance
status paragraph:

```markdown
The 2026-07-10 documentation-toolchain follow-up added a locked, isolated
MkDocs 1.x environment and strict pull-request site build without changing the
publication mechanism.
```

Add this active tooling priority after the frontend audit priority:

```markdown
- Keep the locked docs-only uv environment and strict MkDocs pull-request build
  aligned with the existing GitHub Pages publication workflow.
```

In Future Work, change the maintenance-follow-up list so it names only
`historical-script ownership` and `focused backend service maintainability
work`, removing the completed docs-toolchain item.

Change the roadmap current-status date and both README current-baseline dates
from `2026-07-05` to `2026-07-10` so the existing status-alignment guard remains
green.

Add this plan to `docs/planning/README.md` under closed delivered artifacts:

```markdown
- `docs/superpowers/plans/2026-07-10-reproducible-mkdocs-toolchain.md` (closed, delivered)
```

- [ ] **Step 3: Run complete feasible verification**

Run:

```bash
cd backend
uv lock --check
TMPDIR=/tmp TMP=/tmp TEMP=/tmp .venv/bin/python -m pytest tests/unit -v
cd ..
UV_PROJECT_ENVIRONMENT=.venv-docs uv sync \
  --project backend --locked --only-group docs
UV_PROJECT_ENVIRONMENT=.venv-docs uv run \
  --project backend --no-sync mkdocs build --strict --config-file mkdocs.yml
bash scripts/check-docs.sh
git diff --check
git status --short --branch
```

Expected: the lock is current; the complete backend unit suite, strict site build, and repository docs checks pass; the diff has no whitespace errors; only planned branch changes remain. Record exact test counts and any prerequisite-dependent skips in this plan.

- [ ] **Step 4: Mark the plan complete and commit documentation**

Mark every checkbox in this plan complete and add a status paragraph containing the exact successful commands and test counts from Step 3. Then commit:

```bash
git add README.md CONTRIBUTING.md docs/development/documentation-guidelines.md \
  docs/maintenance-audit.md docs/planning/roadmap.md \
  docs/planning/README.md \
  docs/superpowers/plans/2026-07-10-reproducible-mkdocs-toolchain.md
git commit -m "docs: record reproducible MkDocs validation"
```

- [ ] **Step 5: Review, push, and open a non-merged pull request**

Run a read-only review of `origin/main...HEAD`, fix all Critical and Important
issues, rerun affected verification, then push and create a ready pull request:

```bash
git push -u origin codex/docs-toolchain-reproducibility
gh pr create \
  --base main \
  --head codex/docs-toolchain-reproducibility \
  --title "build: make MkDocs validation reproducible" \
  --body-file /tmp/waittimecanada-mkdocs-pr.md
```

The PR body must summarize the locked docs group, isolated environment, strict
Docs CI lane, deployment parity, verification evidence, and explicit no-deploy
boundary. Wait for required GitHub checks on the exact head. Do not merge the
PR because its changed documentation paths trigger the existing deployment
workflow on main.
