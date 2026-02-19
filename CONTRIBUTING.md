# Contributing to Wait Time Canada

Thanks for contributing to Wait Time Canada.

This repository is a clinical data observatory. Contributions should prioritize methodological clarity, auditability, and operational safety over feature volume.

## Community Standards

When contributing, please:

- Follow our governance policies in `LICENSE` and `CHANGELOG.md`
- Use GitHub issue templates for feature requests and data quality reports
- Follow the Pull Request template for all contributions
- Respect all contributors and maintainers

## Before You Start

- Read `AGENTS.md` for security and attribution constraints.
- Read `docs/development/setup.md` for current environment setup.
- Read `docs/development/testing-guidelines.md` for test expectations.
- Read `docs/reference/data-dictionary.md` for schema details.
- Read `docs/architecture/data-flow.md` for system context.
- Check active priorities in `docs/planning/roadmap.md`.

## Environment Setup

From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'

cd frontend
npm install
cd ..

pre-commit install
```

Copy environment templates and populate local values:

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

Never commit secrets.

## Branch and PR Workflow

- Branch from `main`.
- Use focused branches: `feature/*`, `fix/*`, `docs/*`, `chore/*`.
- Open PRs targeting `main`.
- Keep PRs small enough to review in one pass.

Example:

```bash
git checkout main
git pull origin main
git checkout -b feature/analytics-region-coverage
```

## Quality Gates

Run only the checks relevant to the files you changed.

### Backend

```bash
ruff check backend/src backend/tests
ruff format --check backend/src backend/tests
mypy backend/src
python -m pytest backend/tests
```

### Frontend

```bash
cd frontend
npm run lint
npm run format:check
npm run type-check
npm run test:unit
```

Do not run Playwright locally unless debugging a specific E2E failure. E2E runs in CI.

### Documentation

```bash
bash scripts/check-docs.sh
```

## Testing Expectations

- Add or update tests for behavior changes.
- Prefer deterministic unit tests with clear fixtures.
- For DB-dependent backend behavior, add integration tests with scoped test data.
- Keep ontology and comparability logic explicitly covered.

## Documentation Expectations

Update documentation in the same PR when you change:

- API routes or response contracts
- database schema or migration flow
- operational workflows, scripts, or required secrets
- roadmap or milestone status

Minimum docs update targets:

- `docs/planning/roadmap.md` (status)
- relevant docs under `docs/architecture/` or `docs/API.md`
- `README.md` if setup or behavior changes are user-visible

## Architecture Decisions

Use ADRs for decisions that alter durable architecture, contracts, or operational policy.

- ADR directory: `docs/adr/`
- Template: `docs/adr/template.md`

## Commit Guidance

Use Conventional Commit style when possible:

- `feat:` new functionality
- `fix:` bug fix
- `docs:` documentation-only change
- `refactor:` internal restructure without behavior change
- `test:` test additions/changes
- `chore:` maintenance

Example:

```bash
git commit -m "docs(contributing): align workflow with npm/main and active CI"
```

Only humans should be listed as commit authors and contributors.

## Pull Request Checklist

Before requesting review:

- [ ] Relevant quality gates pass locally
- [ ] Documentation updated for changed behavior
- [ ] No secrets added
- [ ] Roadmap updated if milestone/task status changed
- [ ] PR description includes scope, risk, and verification notes
