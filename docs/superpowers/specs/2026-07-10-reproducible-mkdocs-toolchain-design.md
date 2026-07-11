# Reproducible MkDocs Toolchain Design

## Context

The July 2026 maintenance audit records one concrete tooling gap: the repository
can run `scripts/check-docs.sh` locally, but `mkdocs build --strict` is not part
of the reproducible local or pull-request validation path. The documentation
deployment workflow currently installs floating MkDocs packages with `pip`, so
the deployed site and contributor checks are not tied to the checked-in
`backend/uv.lock` dependency baseline.

The latest successful documentation deployment on 2026-07-10 resolved MkDocs
1.6.1, Material for MkDocs 9.7.6, and mkdocs-minify-plugin 0.8.0. The repository
must remain on MkDocs 1.x until the separately documented migration gate is
opened.

## Decision

Add a dedicated `docs` dependency group to `backend/pyproject.toml` and resolve
it in `backend/uv.lock`. The direct constraints will preserve the current major
version boundaries:

- `mkdocs>=1.6.1,<2`
- `mkdocs-material>=9.7.6,<10`
- `mkdocs-minify-plugin>=0.8,<1`

Use `uv sync --locked --only-group docs` so documentation jobs install only the
locked documentation toolchain rather than the backend runtime. Set
`UV_PROJECT_ENVIRONMENT=.venv-docs` so local documentation checks do not replace
or prune packages in the backend development environment. Ignore
`backend/.venv-docs/` as generated local state.

Both documentation workflows will install the repository-pinned uv version,
use Python 3.12, and select the same locked dependency group. Pull requests will
run `mkdocs build --strict`; the deployment workflow will continue using
`mkdocs gh-deploy --force`, but through the locked environment and with strict
mode explicit.

## Components

### Dependency contract

`backend/pyproject.toml` owns the direct documentation requirements and
`backend/uv.lock` owns exact resolved versions and hashes. This reuses the
repository's existing Python dependency governance instead of introducing a
second requirements file or floating one-shot tool invocation.

### Isolated documentation environment

Commands set `UV_PROJECT_ENVIRONMENT=.venv-docs` while discovering the project
through `--project backend`. The environment path therefore resolves under the
backend project root, remains separate from `backend/.venv`, and is excluded
from version control.

### Pull-request validation

`.github/workflows/docs-ci.yml` retains `scripts/check-docs.sh` and adds a
strict MkDocs site build. Its path filters include `backend/uv.lock` explicitly
so a lock-only change cannot bypass documentation validation.

### Deployment parity

`.github/workflows/deploy-docs.yml` replaces floating `pip install` commands
with the same pinned uv and locked docs-group setup used by Docs CI. It retains
the existing GitHub Pages deployment mechanism and permissions. This batch does
not dispatch, merge, deploy, publish, or otherwise exercise the deployment
step; it stops at a ready pull request because merging documentation changes
would trigger the existing main-branch deployment workflow.

### Contributor entry point

Add a `docs-build` Make target and document it in contributor and documentation
guidance. The target performs the locked docs-group sync and strict build from
the repository root, making the supported command discoverable without asking
contributors to activate either virtual environment manually.

## Command Flow

1. Install the repository-pinned uv version if it is not already available.
2. Set `UV_PROJECT_ENVIRONMENT=.venv-docs`.
3. Run `uv sync --project backend --locked --only-group docs`.
4. Run `uv run --project backend --no-sync mkdocs build --strict --config-file mkdocs.yml`.
5. In the deployment workflow only, replace `build` with
   `gh-deploy --strict --force`; no implementation-time validation invokes that
   command.

MkDocs resolves documentation and output paths relative to `mkdocs.yml`, while
uv's `--project backend` selects the backend lock and environment without
changing the command's repository-root working directory.

## Failure Behavior

- `--locked` fails before installation if `pyproject.toml` and `uv.lock` drift.
- `--only-group docs` prevents unrelated backend runtime packages from becoming
  an implicit requirement of documentation validation.
- `--no-sync` prevents the run step from changing the already-validated
  environment selection.
- MkDocs strict mode turns warnings, invalid navigation, missing referenced
  files, and plugin/configuration failures into a non-zero result.
- Docs CI fails before merge when either the repository documentation checks or
  strict site build fails.
- The deploy job fails before modifying `gh-pages` when locked dependency setup
  or strict site generation fails.

## Test Strategy

Use test-driven changes:

1. Add repository tests that require a `docs` dependency group, the isolated
   environment, locked workflow commands, strict Docs CI build, and lockfile
   path coverage.
2. Run those tests before implementation and confirm they fail on the current
   floating-toolchain workflows.
3. Add the dependency group, regenerate the lock, and update both workflows,
   Makefile, ignores, and contributor documentation.
4. Run the focused tests, `uv lock --check`, the isolated locked sync, the
   strict MkDocs build, `scripts/check-docs.sh`, and `git diff --check`.
5. Run the complete feasible backend unit suite because project metadata and
   workflow-contract tests changed.
6. Push the branch, require GitHub Docs CI to pass on the exact head, and leave
   the pull request open for explicit merge/deployment authorization.

## Alternatives Considered

1. **Locked uv dependency group (selected).** Reuses the checked-in lock,
   isolates the docs environment, and makes local, CI, and deployment versions
   converge.
2. **Pinned `requirements-docs.txt`.** Simple to install, but creates a second
   dependency-maintenance path and does not lock transitive packages or hashes
   without another generated artifact.
3. **Pinned `uvx` invocation.** Avoids a project environment, but repeats
   package constraints across commands and does not make the complete resolved
   environment part of the repository lock.

## Completion Criteria

- The documentation toolchain is represented in `backend/uv.lock`.
- Local strict builds use an ignored environment separate from `backend/.venv`.
- Docs CI runs both repository documentation checks and a strict site build.
- Deployment uses the same locked direct and transitive versions as validation.
- Workflow-contract tests prevent a return to floating installs or omitted
  lockfile path coverage.
- Contributor documentation exposes one supported strict-build command.
- The maintenance audit and roadmap no longer list docs-toolchain availability
  as unfinished work.
- A reviewed, green pull request exists, but it is not merged and no deployment
  is triggered without explicit authorization.
