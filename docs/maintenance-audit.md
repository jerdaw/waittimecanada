# Maintenance Audit

## Audit Metadata

- Audit date: 2026-07-05
- Target repository root: current Git repository root. Exact local filesystem
  path intentionally omitted from this public report.
- Prompt-pack root: user-supplied external v5 deep-evidence repo-health prompt
  pack containing `RUN_THIS_FIRST.md` and the required pass files. Exact local
  filesystem path intentionally omitted from this public report.
- Branch/status at start of v5 continuation: `main...origin/main` with existing
  uncommitted maintenance changes from the earlier audit pass.
- Report location: `docs/maintenance-audit.md`.
- Safety constraints followed: prompt pack treated read-only; no deploys,
  production migrations, production data writes, secret-file inspection,
  framework migrations, or broad dependency upgrades.

## Repo Profile

- Purpose: public-interest health systems observatory for Canadian emergency
  department wait-time methodology, provenance, data quality, public-health
  resource overlays, analytics, and documentation.
- Audience: public repository readers, project maintainers, contributors, and
  operators using reproducible local workflows.
- Risk level: health-adjacent public information with clinical-safety,
  provenance, privacy, and public documentation boundaries. The repository does
  not handle individual patient records.
- Backend stack: Python 3.12+, `uv`, pytest, Ruff, mypy, Bandit, PostgreSQL,
  psycopg2, Pydantic, scraper/services CLI modules.
- Frontend stack: Next.js 15 App Router, TypeScript, Mapbox GL JS, Vitest,
  React Testing Library, Playwright E2E lanes.
- Database stack: SQL migrations under `backend/migrations`, checksum-ledger
  migration runner, ontology enums/checks, raw measurement retention, permanent
  aggregate tables.
- Automation: GitHub Actions, `Makefile`, root scripts, backend scripts,
  frontend npm scripts, docs quality script, Dependabot config.

## Instructions And Conventions Considered

- `AGENTS.md`: no direct inspection of `.env`, `.env.local`, key, certificate,
  or private credential files; placeholder-only env examples; human authorship;
  public documentation boundary; ontology/provenance/clinical safety guardrails.
- `README.md`, `CONTRIBUTING.md`, `backend/README.md`, `frontend/README.md`:
  current setup, quality gates, and public project framing.
- `backend/pyproject.toml`, `frontend/package.json`, `Makefile`, GitHub
  workflows: authoritative commands and runtime/package manager choices.
- `docs/development/*`, `docs/architecture/*`, `docs/reference/*`,
  `docs/adr/index.md`, `backend/migrations/README.md`: docs and architecture
  contracts.

## Reviewable Inventory And Coverage Tier

Inventory commands:

- `pwd`
- `git rev-parse --show-toplevel`
- `git status --short --branch`
- `git status --short --ignored`
- `git ls-files`
- `find . -maxdepth 3 ...` excluding dependency, private, cache, build, and
  secret-pattern paths
- Reviewable-file classification script over `git ls-files`, excluding locks,
  binary assets, generated/cache trees, and secret-pattern files

Inventory results:

| Area | Reviewable files | Approx. lines |
| --- | ---: | ---: |
| Backend source | 49 | 13,682 |
| Backend tests | 68 | 13,765 |
| Backend scripts/tools | 14 | 2,759 |
| Database/data/migrations | 41 | 3,245 |
| Frontend source | 128 | 27,237 |
| Frontend tests | 73 | 9,278 |
| Docs/governance | 133 | 18,668 |
| CI/GitHub | 22 | 1,663 |
| Config/tooling | 20 | 1,003 |
| Repo scripts | 6 | 1,122 |
| Other tracked text | 15 | 1,052 |
| Total reviewable text | 569 | 93,474 |

Coverage tier: medium. The repo has 579 tracked files and 569 reviewable text
files after exclusions, under the large-repo file threshold but near the upper
end of medium. This audit inspected all central/high-risk surfaces and a
representative slice of each major subsystem rather than every line.

Important exclusions:

- Dependency/build/cache trees: `.git`, `frontend/node_modules`, backend
  virtualenv, `.next`, coverage outputs, `.pytest_cache`, `.mypy_cache`,
  `.ruff_cache`, `__pycache__`.
- Lockfiles were checked for presence/consistency, not manually reviewed
  line-by-line.
- Secret/private paths and ignored local env files were not inspected.
- Archived planning notes were searched when relevant but not rewritten unless
  active docs pointed to stale state.

## Pass Sequence

The required sequence was followed without reordering:

1. General code quality, docs, and maintenance
2. Test coverage and regression protection
3. Security, privacy, and secrets handling
4. CI, automation, and developer workflow
5. Dependency and package hygiene
6. Documentation and onboarding
7. Architecture and maintainability
8. Performance and scalability
9. Database, data, and migration health
10. Release readiness
11. Public repository presentation

## Command And Search Ledger

| Command/search | Result | Notes |
| --- | --- | --- |
| `git status --short --branch` | Passed | Existing uncommitted maintenance diff preserved. |
| `git ls-files` | Passed | 579 tracked files. |
| Reviewable inventory script | Passed | 569 reviewable text files, about 93k lines. |
| `rg "TODO|FIXME|HACK|XXX|debugger|console\\.log|console\\.debug"` with secret/private/cache exclusions | Passed | Remaining app-source `console.log` is the shared logger fallback; test/demo/doc examples are intentional. |
| Env-var search over code/docs/config | Passed | Drove updates for `DATABASE_SSL_MODE` and `OPERATIONAL_NOTIFICATION_MODE`. |
| Error/query/security sink search over backend/frontend/scripts | Passed | Identified raw error-message response pattern; the focused API-hardening follow-up was completed on 2026-07-10. Reviewed `sql.unsafe`/psycopg2 parameterization surfaces. |
| Tracked secret-pattern scan with `git grep` and secret/lock exclusions | Passed | No tracked high-signal secret patterns matched. |
| `uv lock --check` | Passed | Pyproject metadata change did not require lockfile update. |
| `uv tree --depth 1` | Passed | Dependency tree inspected; no upgrades made. |
| `npm audit --omit=dev --audit-level=high` | Passed | `0 vulnerabilities`. |
| `npm ls --depth=0` | Passed with local noise | Reports ignored local `node_modules` extraneous `@emnapi/runtime`; no tracked change. |
| `uv run ruff check src tests scripts` | Passed | Backend lint. |
| `uv run ruff format --check src tests scripts` | Passed | `125 files already formatted`. |
| `uv run mypy src` | Passed | `49 source files`. |
| `uv run bandit -r src -q` | Passed | No Bandit findings printed. |
| `uv run python scripts/check_migration_sequence.py` | Passed | Migration sequence guard passed. |
| `TMPDIR=/tmp TMP=/tmp TEMP=/tmp uv run pytest tests` | Passed | `571 passed, 27 skipped`. |
| `npm run lint` | Passed | Frontend ESLint. |
| `npm run format:check` | Passed | Prettier check. |
| `npm run type-check` | Passed | App TypeScript. |
| `npm run type-check:test` | Passed | Test TypeScript. |
| `npm run test:unit` | Passed | `79 passed` test files, `441 passed`; existing jsdom navigation warning observed. |
| Frontend `npm run build` with placeholder DB/Mapbox env | Passed | Next build completed; framework reported `.env.local` auto-load, no values inspected or printed. |
| `npm run test:unit -- utils/rate-limit.test.ts` | Failed then passed | Expected red/green cycle for raw-IP logging regression. |
| `TMPDIR=/tmp TMP=/tmp TEMP=/tmp uv run pytest tests/unit/test_pyproject_scripts.py` | Failed then passed | Expected red/green cycle for broken package script metadata. |
| Plain `uv run pytest ...` without temp override | Failed locally | Known pytest capture cleanup issue when local temp vars point outside Linux temp. |
| `mkdocs build --strict` | Could not run | `mkdocs` not installed in this shell. |

## Baseline Verification

Baseline and targeted checks established the repo's strongest feasible local
verification set:

- Backend: Ruff lint/format, mypy, migration sequence, Bandit, pytest.
- Frontend: ESLint, Prettier, TypeScript app/test projects, Vitest, Next build,
  npm audit, npm dependency tree.
- Docs/tooling: docs script, markdown/public-boundary/static guards, diff
  whitespace check, migration docs/search probes.

The known prerequisite-dependent lanes remain out of default local scope:

- Database-backed integration and E2E tests skip without a test `DATABASE_URL`.
- Frontend Playwright E2E is CI/manual-dispatch oriented.
- Production smoke/deployment workflows were not run.
- `mkdocs build --strict` needs the docs toolchain installed.

## Pass Completion Table

| Pass | Status | Evidence summary |
| --- | --- | --- |
| 1. General code quality/docs/maintenance | Fixed changes | Hospital pagination/cache mismatch fixed; stale migration docs and dead package entrypoints fixed; noisy logs reduced. |
| 2. Test coverage/regression | Fixed changes | Added hospital pagination, validation, rate-limit privacy, and package-script metadata regression coverage. |
| 3. Security/privacy/secrets | Fixed changes + follow-up completed | Removed browser coarse-location/service-worker success logs; removed raw client-IP rate-limit warning; scans passed; API error response hardening completed on 2026-07-10. |
| 4. CI/automation/workflow | Fixed changes | CONTRIBUTING, setup docs, `Makefile`, docs index, and backend metadata aligned with existing locked workflows. |
| 5. Dependency/package hygiene | Fixed changes | Removed broken package console scripts; no dependency upgrades or lockfile churn. |
| 6. Documentation/onboarding | Fixed changes | Active setup, env, ADR, API/OpenAPI, migration, testing, and maintenance-audit docs updated. |
| 7. Architecture/maintainability | Fixed local mismatch | Preserved architecture; localized hospital query validation/cache/data-access alignment; no broad refactor. |
| 8. Performance/scalability | Fixed local issue + deferred follow-up | Added opt-in bounded hospital API pagination and cache-key distinction; cursor pagination deferred as API contract work. |
| 9. Database/data/migration health | Fixed docs/tests only | Migration docs/examples fixed; the 2026-07-10 follow-up reconciled every history heading and added CI-enforced inventory/count/next-prefix/placeholder checks; no schema or data changes. |
| 10. Release readiness | No deploy/release; verification passed | Full feasible local checks passed; release/deploy owner actions deferred. |
| 11. Public repo presentation | Fixed docs clarity | Public docs index/report/API/setup presentation improved without adding private operations details. |

## Pass Evidence

### 1. General Code Quality, Docs, And Maintenance

Scope decision:

- Applies to frontend API route correctness, validation schemas, backend package
  metadata, active docs, scripts, and public logs.
- Avoided broad rewrites and archived-doc churn.

Surfaces inspected:

- `frontend/app/api/hospitals/route.ts`
- `frontend/utils/validations.ts`
- `frontend/utils/server-cache.ts`
- `frontend/utils/rate-limit.ts`
- `frontend/app/[locale]/page.tsx`
- `frontend/components/ServiceWorkerRegister.tsx`
- `backend/pyproject.toml`
- `backend/src/waittime/cli/*`
- `README.md`, `CONTRIBUTING.md`, `backend/README.md`, `frontend/README.md`
- `backend/migrations/README.md`, `docs/development/database-migrations.md`
- `scripts/check-docs.sh`

Searches/probes:

- Debug marker search for TODO/FIXME/HACK/debugger/console success logs.
- `rg "export_json|populate_seed_data"` to verify broken script references.
- `git diff` review of existing hospital route, validation, docs, and logging
  changes.
- Targeted rate-limit and pyproject script tests.

Candidate findings considered:

- Fixed: `/api/hospitals` accepted `page`/`limit` but ignored them.
- Fixed: hospital cache keys did not distinguish paginated requests.
- Fixed: hospital validation injected defaults even when pagination was absent.
- Fixed: stale migration examples still pointed to `020`/`021`.
- Fixed: backend package console scripts referenced missing modules.
- Fixed: raw IP warning log in rate limiter.
- Not an issue: shared `frontend/utils/logger.ts` console fallback is expected
  for browser/edge environments.
- Resolved in the 2026-07-10 focused follow-up: exception-derived public API
  500 response values are centrally redacted without changing response shapes.

Change gate:

- Implemented changes are local, tested, and follow existing TypeScript/Vitest,
  Python/pytest, docs, and package metadata patterns.
- No public route defaults were broken; `/api/hospitals` remains unpaginated by
  default for map/list behavior.

Verification:

- Targeted Vitest and pytest checks passed.
- Final backend/frontend quality gates passed.

### 2. Test Coverage And Regression Protection

Scope decision:

- Applies because behavior/config fixes were made and the repo has strong
  pytest/Vitest patterns.
- Avoided adding frameworks, coverage thresholds, or service-dependent tests.

Surfaces inspected:

- `frontend/app/api/hospitals/route.test.ts`
- `frontend/utils/validations.test.ts`
- `frontend/utils/rate-limit.test.ts`
- `frontend/utils/rate-limit.integration.test.ts`
- `backend/tests/unit/test_check_migration_sequence.py`
- `backend/tests/unit/test_seed_cli.py`
- New `backend/tests/unit/test_pyproject_scripts.py`

Searches/probes:

- Test file inventory under `backend/tests` and `frontend/tests`.
- Targeted failing tests for rate-limit privacy and pyproject script metadata.
- Full backend and frontend unit test runs.

Candidate findings considered:

- Fixed: missing regression for explicit hospital pagination.
- Fixed: missing assertion that omitted hospital pagination stays omitted.
- Fixed: missing regression preventing raw client IPs in rate-limit warnings.
- Fixed: missing guard that declared package console scripts resolve.
- Already satisfied: ontology and comparability tests are broad and passed.
- Deferred: Playwright E2E remains CI/manual-dispatch oriented.

Change gate:

- Tests use existing local patterns and no new dependencies.
- Package metadata test checks importability/callability without invoking
  external services.

Verification:

- `npm run test:unit -- utils/rate-limit.test.ts app/api/hospitals/route.test.ts utils/validations.test.ts`: passed.
- `TMPDIR=/tmp TMP=/tmp TEMP=/tmp uv run pytest tests/unit/test_pyproject_scripts.py tests/unit/test_check_migration_sequence.py`: passed.
- Full backend/frontend test suites passed.

### 3. Security, Privacy, And Secrets Handling

Scope decision:

- Applies because the repo has env examples, public APIs, browser logging,
  scraper/database code, and public docs boundaries.
- Formal exhaustive security scanning was not folded into this run because it is
  a separate workflow with heavier artifacts and would exceed the bounded
  repo-health objective.

Surfaces inspected:

- `AGENTS.md`, `SECURITY.md`, `.pre-commit-config.yaml`
- `backend/.env.example`, `frontend/.env.example`,
  `frontend/.env.local.example`
- `frontend/app/api/*/route.ts` error/logging/search surfaces
- `frontend/utils/rate-limit.ts`, `frontend/utils/db.ts`,
  `frontend/utils/logger.ts`
- `backend/src/waittime/services/database.py`
- `backend/src/waittime/services/alerts.py`
- `scripts/check-docs.sh`

Searches/probes:

- Tracked high-signal secret pattern scan with lock/secret/private exclusions.
- Env-var usage search across code/docs/config.
- Search for `sql.unsafe`, psycopg2 `execute`, `subprocess`, `eval`,
  `dangerouslySetInnerHTML`, and raw error-message response patterns.
- `uv run bandit -r src -q`.
- `npm audit --omit=dev --audit-level=high`.
- Docs guardrail checks for human authorship, public-boundary terms, file links,
  ontology safety, and clinical-safety language.

Candidate findings considered:

- Fixed: homepage IP-geolocation success path logged coarse city/region in the
  browser console.
- Fixed: service worker registration success path logged registration scope.
- Fixed: rate limiter logged raw client IP on 429.
- Already satisfied: tracked env examples are placeholders; secret-pattern scan
  found no high-signal tracked matches.
- Already satisfied: database query code inspected uses parameter binding for
  dynamic user values in reviewed surfaces.
- Resolved in the 2026-07-10 focused follow-up: public API 500 responses retain
  internal logging while returning a generic exception-derived message.
- Deferred: install/use a Python dependency vulnerability scanner if owners want
  a routine local advisory check; current CI/dependency posture uses Bandit and
  Dependabot.

Change gate:

- Logging fixes are privacy-preserving, behavior-compatible, and covered by
  existing tests where behavior matters.
- No secret files were read or summarized.

Verification:

- Secret-pattern scan: no matches.
- Bandit: passed.
- npm audit: passed.
- Rate-limit privacy test: failed before fix, passed after fix.
- Docs guardrails: checked via `scripts/check-docs.sh`.

Security/privacy notes:

- No `.env`, `.env.local`, key, certificate, or private credential file was
  directly inspected.
- Framework/tooling may auto-load local env files during trusted build commands;
  no loaded values were printed, inspected, copied, or persisted.
- Placeholder test credentials in commands are non-production examples.

### 4. CI, Automation, And Developer Workflow

Scope decision:

- Applies because the repo has GitHub Actions, Makefile targets, docs scripts,
  backend/frontend package scripts, and documented local quality gates.
- Avoided changing deploy/release workflows or adding process machinery.

Surfaces inspected:

- `.github/workflows/frontend-ci.yml`
- `.github/workflows/scraper-ci.yml`
- `.github/workflows/docs-ci.yml`
- `.github/dependabot.yml`
- `.pre-commit-config.yaml`
- `Makefile`
- `CONTRIBUTING.md`
- `scripts/check-docs.sh`
- `backend/pyproject.toml`, `frontend/package.json`

Searches/probes:

- Workflow reads for Node/Python/uv/npm command alignment.
- Docs grep for `npm install`, `.venv/bin`, pytest command drift, migration
  numbering, and env-var documentation.
- `make -n test-e2e` earlier verified the command shape.

Candidate findings considered:

- Fixed: CONTRIBUTING used older root virtualenv/pip workflow.
- Fixed: active frontend setup docs used `npm install` rather than lockfile
  `npm ci`.
- Fixed: `make test-e2e` referenced an obsolete `.venv/bin/pytest` path.
- Fixed: docs index pointed latest maintenance log at an older archived note.
- Already satisfied: CI uses pinned setup actions, locked backend/frontend
  installs, manual dispatch for heavier E2E, and docs CI fetches full history
  for authorship checks.
- Deferred: production/operational workflow cadence changes require owner
  release/operations decisions.

Change gate:

- Documentation/script changes align with existing `uv` and npm workflows.
- No CI provider, hook, or release process was added.

Verification:

- Backend/frontend final gates passed.
- Docs script passed after report updates.

### 5. Dependency And Package Hygiene

Scope decision:

- Applies to `backend/pyproject.toml`, `backend/uv.lock`,
  `frontend/package.json`, `frontend/package-lock.json`, `.nvmrc`,
  Dependabot, Docker/config files, and install docs.
- Avoided upgrades and lockfile churn unless required.

Surfaces inspected:

- `backend/pyproject.toml`
- `backend/uv.lock`
- `frontend/package.json`
- `frontend/package-lock.json`
- `.nvmrc`
- `.github/dependabot.yml`
- `.pre-commit-config.yaml`
- `frontend/Dockerfile`

Searches/probes:

- `uv lock --check`
- `uv tree --depth 1`
- `npm audit --omit=dev --audit-level=high`
- `npm ls --depth=0`
- Static check that pyproject script entry points resolve.

Candidate findings considered:

- Fixed: `export_json` and `populate_seed_data` console scripts pointed to
  missing modules.
- Already satisfied: backend lock remained consistent after metadata-only
  script cleanup.
- Already satisfied: npm audit found no production high-or-higher
  vulnerabilities.
- Local-only: ignored `node_modules` reports extraneous `@emnapi/runtime`; not a
  tracked repository issue.
- Deferred: broad version freshness is separate dependency-maintenance work.

Change gate:

- Removed only broken package metadata; no dependency versions changed.
- Added a package metadata regression test to avoid recurrence.

Verification:

- `uv lock --check`: passed.
- `TMPDIR=/tmp TMP=/tmp TEMP=/tmp uv run pytest tests/unit/test_pyproject_scripts.py`: failed before fix, passed after fix.
- Full backend tests and lint/format passed.

### 6. Documentation And Onboarding

Scope decision:

- Applies because active docs explain setup, testing, migrations, APIs,
  environment variables, architecture, and public presentation.
- Archived historical docs were not broadly rewritten.

Surfaces inspected:

- `README.md`
- `CONTRIBUTING.md`
- `backend/README.md`
- `frontend/README.md`
- `docs/README.md`
- `docs/API.md`
- `docs/openapi.yaml`
- `docs/reference/environment-variables.md`
- `docs/development/setup.md`
- `docs/development/testing-guidelines.md`
- `docs/development/database-migrations.md`
- `docs/adr/index.md`
- `backend/migrations/README.md`

Searches/probes:

- Docs grep for stale install commands, migration numbers, ADR index drift,
  undocumented env vars, and active cadence wording.
- `bash scripts/check-docs.sh`.
- Broken-link/public-boundary checks embedded in the docs script.

Candidate findings considered:

- Fixed: migration count/next-number docs and examples were stale; the
  2026-07-10 follow-up also reconciled missing history entries and extended the
  existing sequence guard to prevent repeat drift.
- Fixed: ADR index omitted existing ADRs.
- Fixed: root README hard-coded stale ADR count.
- Fixed: `DATABASE_SSL_MODE` and `OPERATIONAL_NOTIFICATION_MODE` docs/examples
  were incomplete.
- Fixed: active setup docs now prefer `npm ci`.
- Fixed: docs index now points to this maintenance audit.
- Already satisfied: clinical-safety and comparability guardrails remain present
  in active docs.

Change gate:

- Docs changes describe current behavior and commands; no new docs system or
  private operations material added.

Verification:

- `bash scripts/check-docs.sh`: passed after the report was updated.
- Markdown/link/public-boundary checks passed.

### 7. Architecture And Maintainability

Scope decision:

- Applies to architecture docs, domain models/enums, service boundaries,
  frontend API route patterns, shared cache/db/rate-limit helpers, migrations,
  and tests.
- Avoided broad restructuring, new abstractions, or public API changes.

Surfaces inspected:

- `docs/architecture/index.md`, `docs/architecture/api.md`,
  `docs/architecture/database.md`, `docs/architecture/data-flow.md`
- `backend/src/waittime/core/enums.py`
- `backend/src/waittime/core/models.py`
- `backend/src/waittime/services/database.py`
- `backend/src/waittime/services/runtime_config.py`
- `frontend/app/api/hospitals/route.ts`
- `frontend/utils/db.ts`, `frontend/utils/server-cache.ts`,
  `frontend/utils/validations.ts`, `frontend/utils/rate-limit.ts`

Searches/probes:

- Manual reads of architecture docs, domain models, database service, runtime
  config, frontend DB/cache/validation helpers, and the hospital route.
- Import and package-entrypoint search for CLI metadata drift.
- Query/error/logging searches from the command ledger to identify coupling,
  raw error response patterns, and route/helper responsibility boundaries.
- Final backend/frontend lint, type, test, and build checks to validate that
  local maintainability changes did not break contracts.

Architecture map:

- Backend scrapers normalize public source payloads into ontology-tagged
  `Measurement` records and source/hospital metadata.
- `DatabaseService` centralizes PostgreSQL persistence through psycopg2 and
  parameterized queries.
- Aggregation, benchmarking, trends, data-quality, alerting, geocoding, and
  public-health resource logic live in focused backend service modules.
- Next.js API routes read PostgreSQL through shared frontend DB/cache utilities,
  validate query params through Zod schemas, and expose public JSON endpoints.
- Frontend pages/components render map, analytics, data-quality, methods,
  resources, and status views with targeted Vitest/Playwright coverage.
- Migration files and ADRs preserve schema and architecture history.

Candidate findings considered:

- Fixed: hospital route validation/cache/data-access behavior was internally
  inconsistent.
- Fixed: package entrypoint metadata referenced nonexistent CLI modules.
- Already satisfied: ontology enums and AGENTS guardrail constants match via
  docs script check.
- Deferred: `DatabaseService` is large; splitting it would be a broad refactor
  requiring a focused design pass.
- Resolved in the 2026-07-10 focused follow-up: all 17 route handlers that
  exposed exception-derived values now share the same redaction utility.

Change gate:

- Implemented changes are local and use existing route/schema/test/doc patterns.
- No module moves or architecture-pattern changes were made.

Verification:

- Full backend and frontend verification passed.

### 8. Performance And Scalability

Scope decision:

- Applies to public API routes, DB query bounds, caching keys, index support,
  frontend rendering/data loading, scraper jobs, cleanup/aggregation flows, and
  docs check cost.
- Avoided speculative profiling infrastructure, new caches, queues, or schema
  changes.

Surfaces inspected:

- `frontend/app/api/hospitals/route.ts`
- `frontend/utils/server-cache.ts`
- `frontend/utils/rate-limit.ts`
- `backend/migrations/002_create_tables.sql`
- `backend/migrations/012_optimize_indexes.sql`
- `backend/migrations/016_add_measurement_retention_efficiency_guards.sql`
- `backend/src/waittime/services/aggregation.py`
- `backend/src/waittime/services/database.py`
- `docs/adr/0021-bounded-retention-cleanup-operations.md`
- `docs/adr/0022-frontend-read-cache-for-public-load-guardrails.md`

Searches/probes:

- Search for `LIMIT`, `OFFSET`, cache keys, unbounded route queries, and index
  coverage.
- Postgres best-practice review for WHERE/JOIN indexes and pagination tradeoffs.
- Migration index grep for hospital and measurement query support.

Candidate findings considered:

- Fixed: `/api/hospitals` had accepted-but-unused pagination parameters.
- Fixed: paginated hospital requests were not cache-key distinct.
- Already satisfied: migrations include indexes for visible/verified province
  filters and latest measurement lateral lookups.
- Deferred: cursor/keyset pagination is better for deep pages but would change
  API semantics; current offset pagination is opt-in, bounded to 100, and suited
  to current hospital-list size.
- Deferred: full performance profiling and bundle-budget tuning require a
  focused performance run.

Change gate:

- Added `LIMIT/OFFSET` only for explicit pagination, preserving default
  all-hospitals behavior.
- Dynamic values remain parameterized.

Verification:

- Hospital API route tests passed.
- Frontend build/test/type checks passed.

### 9. Database, Data, And Migration Health

Scope decision:

- Applies because the repo has PostgreSQL migrations, seeds, DB services,
  migration docs, and test/database helper scripts.
- No production DB, remote data, destructive migration, or schema change was
  run.

Surfaces inspected:

- `backend/migrations/*.sql`
- `backend/migrations/README.md`
- `docs/development/database-migrations.md`
- `backend/run_migrations.py`
- `backend/scripts/check_migration_sequence.py`
- `backend/tests/unit/test_check_migration_sequence.py`
- `backend/tests/unit/test_run_migrations.py`
- `backend/src/waittime/services/database.py`
- `docker-compose.test.yml`
- `scripts/run-disposable-db-checks.sh`

Searches/probes:

- `ls backend/migrations`
- Migration grep for indexes, constraints, duplicate prefix exception, and next
  migration examples.
- `uv run python scripts/check_migration_sequence.py`
- Targeted migration sequence tests.

Candidate findings considered:

- Fixed: canonical migration README and development guide still had stale
  `020`/`021` examples after the current `021` migration.
- Already satisfied: duplicate `020` prefix is documented as legacy and guarded
  by tests.
- Already satisfied: measurement retention and query indexes exist for reviewed
  hot paths.
- Deferred: adding indexes/migrations without a live EXPLAIN plan was not
  justified.

Change gate:

- Only documentation/tests/package metadata changed in the database pass.
- No data was modified and no migration was created.

Verification:

- Migration sequence command passed.
- Full backend tests passed.

Data safety notes:

- Environments used: local checkout only.
- Migrations created: none.
- Data modified: none.
- Production writes: none.

### 10. Release Readiness

Scope decision:

- Applies to app build, package metadata, license/security/changelog files,
  CI-equivalent checks, docs, environment examples, and release/deploy workflows.
- Publishing, tagging, deploying, version bumps, and release policy changes were
  out of scope.

Surfaces inspected:

- `LICENSE`, `SECURITY.md`, `CHANGELOG.md`, `CITATION.cff`,
  `.zenodo.json`
- `frontend/package.json`, `backend/pyproject.toml`
- `frontend/Dockerfile`, `docker-compose.test.yml`, `lighthouserc.json`
- `.github/workflows/release.yml`, `.github/workflows/production-readiness.yml`,
  `.github/workflows/production-smoke.yml`
- Setup/build/test docs

Searches/probes:

- Full feasible local verification set.
- Package metadata script importability test.
- Docs/public-boundary checks.

Release-readiness checklist:

| Item | Status | Evidence |
| --- | --- | --- |
| License present | Ready | `LICENSE` present. |
| Security policy present | Ready | `SECURITY.md` present and inspected. |
| Backend package metadata | Fixed | Broken console scripts removed; metadata test added. |
| Frontend build | Ready for local verification | Next build passed with placeholders. |
| Tests/lint/type checks | Ready for local verification | Full feasible checks passed. |
| Docs site strict build | Blocked locally | `mkdocs` not installed. |
| DB-backed smoke/E2E | Prerequisite-dependent | Requires test DB/front-end server or CI/manual-dispatch lane. |
| Production deploy/release | Owner decision | Not run or changed. |

Candidate findings considered:

- Fixed: backend package metadata contained dead entry points.
- Fixed: docs/setup command drift could confuse release preparation.
- Already satisfied: license, security policy, CI workflows, and build commands
  are present.
- Deferred: release tagging/deploy verification requires explicit release
  intent.

Change gate:

- Implemented changes are release-adjacent metadata/docs fixes that make the
  existing release/build posture more accurate.
- Publishing, deployment, version bumps, tagging, and production checks were
  intentionally left to owner-controlled release workflows.

Verification:

- Strong local checks passed except docs strict build unavailable.

### 11. Public Repository Presentation

Scope decision:

- Applies because the repo is public-facing and has README/docs/badges,
  contribution/security files, issue/PR templates, public API docs, and public
  health-data claims.
- Avoided marketing rewrites, screenshots, external repo setting changes, or
  private operations content.

Surfaces inspected:

- `README.md`
- `docs/index.md`, `docs/README.md`
- `docs/API.md`, `docs/openapi.yaml`
- `docs/reference/environment-variables.md`
- `CONTRIBUTING.md`, `SECURITY.md`
- `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md`
- `frontend/README.md`, `backend/README.md`

Searches/probes:

- Docs script checks for file links, public-boundary terms, human-authorship
  guardrails, active cadence drift, clinical-safety language, and roadmap
  consistency.
- Docs grep for stale counts, setup commands, env examples, and migration
  numbers.

Candidate findings considered:

- Fixed: docs index pointed to an old maintenance log.
- Fixed: active setup/API/migration/env docs had stale or incomplete public
  reader guidance.
- Already satisfied: public documentation boundary and clinical-safety wording
  remained intact.
- Deferred: screenshots/demo refresh and public landing polish are outside this
  maintenance diff.

Change gate:

- Presentation changes are factual and tied to inspected repo state.
- No private deployment paths, credentials, monitoring secrets, or
  environment-specific production notes were added.

Verification:

- Docs quality script passed.

## Changes Applied

| Area | Files | Summary |
| --- | --- | --- |
| Hospital API behavior | `frontend/app/api/hospitals/route.ts`, `frontend/utils/validations.ts` | Added opt-in `page`/`limit` pagination, parameterized `LIMIT/OFFSET`, and cache-key distinction while preserving default full response. |
| Hospital/validation tests | `frontend/app/api/hospitals/route.test.ts`, `frontend/utils/validations.test.ts` | Added regression coverage for unpaginated defaults and explicit pagination. |
| Privacy logging | `frontend/app/[locale]/page.tsx`, `frontend/components/ServiceWorkerRegister.tsx`, `frontend/utils/rate-limit.ts` | Removed coarse-location/service-worker success logs and stopped logging raw client IPs on rate limits. |
| Privacy tests | `frontend/utils/rate-limit.test.ts` | Added regression that rate-limit warnings do not include raw IPs. |
| Backend package metadata | `backend/pyproject.toml`, `backend/tests/unit/test_pyproject_scripts.py` | Removed two broken console scripts and added an importability/callability metadata test. |
| Workflow docs | `CONTRIBUTING.md`, `Makefile`, setup/testing docs | Aligned local commands with `uv`, `npm ci`, and pytest temp workaround. |
| API/docs | `docs/API.md`, `docs/openapi.yaml`, env docs/examples | Documented optional hospital pagination and missing env settings. |
| Migration docs | `backend/migrations/README.md`, `docs/development/database-migrations.md` | Corrected migration count, current latest migration, next-migration examples, and missing history entries; added CI-enforced README consistency checks on 2026-07-10. |
| Docs navigation | `docs/README.md`, `docs/adr/index.md`, `README.md` | Updated ADR/docs index and removed stale count/link drift. |
| Active instructions/roadmap | `AGENTS.md`, `docs/planning/roadmap.md` | Refreshed local verification counts, session status, and focused follow-up ledger references. |
| Docs checks | `scripts/check-docs.sh` | Included this report in docs quality checks. |

## Tests Added Or Updated

- `frontend/app/api/hospitals/route.test.ts`
  - Asserts unpaginated hospital requests do not add top-level pagination.
  - Asserts explicit `page=2&limit=25` produces parameterized `LIMIT/OFFSET`.
- `frontend/utils/validations.test.ts`
  - Asserts hospital pagination remains optional when absent.
  - Asserts explicit pagination strings are coerced and bounded.
- `frontend/utils/rate-limit.test.ts`
  - Asserts rate-limit warnings do not include raw client IPs.
- `backend/tests/unit/test_pyproject_scripts.py`
  - Asserts backend package console script entry points import and resolve to
    callables.

## Deferred Or Rejected Candidates

| Candidate | Decision | Rationale |
| --- | --- | --- |
| Normalize every public API 500 response to hide raw server error details | Delivered 2026-07-10 | A focused compatibility-preserving pass added centralized redaction and route-by-route tests for all 17 affected handlers. |
| Convert hospital pagination to cursor/keyset pagination | Deferred | Stronger deep-page performance, but changes API contract. Current opt-in offset pagination is bounded and low-risk. |
| Split `DatabaseService` into smaller modules | Deferred | Maintainability value, but large refactor with broad review cost. |
| Add indexes/migrations for speculative query improvements | Rejected for this pass | Existing indexes cover reviewed hot paths; no live EXPLAIN evidence gathered. |
| Upgrade dependencies | Rejected for this pass | No high production npm vulnerabilities found; broad upgrade work belongs in dependency-focused run. |
| Run production smoke/deploy/migrations | Rejected | Requires explicit release/operations intent. |
| Inspect ignored env/private files | Rejected | Violates repo security instructions. |

## Final Verification

Passed:

- `uv lock --check`
- `uv tree --depth 1`
- `uv run ruff check src tests scripts`
- `uv run ruff format --check src tests scripts`
- `uv run mypy src`
- `uv run bandit -r src -q`
- `uv run python scripts/check_migration_sequence.py`
- `TMPDIR=/tmp TMP=/tmp TEMP=/tmp uv run pytest tests`
  - Result: `571 passed, 27 skipped`
- `npm run lint`
- `npm run format:check`
- `npm run type-check`
- `npm run type-check:test`
- `npm run test:unit`
  - Result: `79 passed`, `441 passed`
- `npm run build` with placeholder DB/Mapbox env
- `npm audit --omit=dev --audit-level=high`
  - Result: `0 vulnerabilities`
- `npm ls --depth=0`
  - Passed with ignored local extraneous-package noise.
- `bash scripts/check-docs.sh`
- `git diff --check`

Failed or unavailable:

- Plain backend pytest without the documented temp override failed locally during
  pytest capture cleanup. The documented `TMPDIR=/tmp TMP=/tmp TEMP=/tmp`
  invocation passed.
- `mkdocs build --strict` could not run because `mkdocs` is not installed in
  this shell.

Expected red/green failures during fixes:

- Rate-limit privacy test failed before removing raw IP logging, then passed.
- Package script metadata test failed before removing dead console scripts, then
  passed.
- Earlier hospital pagination and validation tests failed before the hospital
  route/schema fix, then passed.
- Docs quality checks failed on README/roadmap status-date alignment after the
  roadmap update, then passed after the README date was aligned.

## Security And Privacy Notes

- No secret files were directly inspected.
- No tracked high-signal secret patterns were found by the scan performed.
- Browser success logs for IP-derived coarse location and service worker scope
  were removed.
- Rate-limit warnings no longer include raw client IPs.
- Public docs did not gain private operations paths, credentials, or production
  environment details.
- Completed security recommendation: the 2026-07-10 follow-up keeps server
  details in internal logs and removes them from public 500 responses.

## Remaining Recommendations

1. Install the docs toolchain locally if `mkdocs build --strict` should be a
   routine local check.
2. Run the disposable database verification helper before a release when
   database-backed integration, migrations-on-fresh-DB, pipeline smoke, and
   Playwright coverage are required.
3. Consider a focused backend service maintainability pass for the largest
   database service surfaces.
4. Keep dependency upgrades separate unless required by security, compatibility,
   or owner-directed maintenance.

## Final Diff Summary

At pre-commit review time:

- Modified tracked files: 28.
- New untracked files: `backend/tests/unit/test_pyproject_scripts.py` and
  `docs/maintenance-audit.md`.
- Tracked diff summary before staging new files: 28 files changed, 189
  insertions, 70 deletions.
- No deploy, release, production migration, or production data operation was
  performed.

## Risks, Assumptions, And Intentionally Unchanged Areas

- `/api/hospitals` remains unpaginated by default to preserve map/list behavior.
- Explicit hospital pagination uses bounded offset pagination; deep cursor
  pagination remains a future API decision.
- DB-backed integration, smoke, and E2E lanes are prerequisite-dependent and
  were not forced locally.
- `mkdocs build --strict` remains unavailable until the docs toolchain is
  installed.
- Ignored local dependency/cache/env/private trees were not inspected.
- Generated verification artifacts were cleaned; ignored env, dependency, and
  private trees remain untouched.

## Professionalization Pass Addendum (2026-07-05)

### Metadata

- Audit date: 2026-07-05.
- Pass: code-adjacent writing professionalization.
- Prompt-pack root: external v6 professionalization prompt pack located outside
  the repository; exact local filesystem path intentionally omitted from this
  public report.
- Branch/status at start: `main...origin/main` with no uncommitted tracked
  changes.
- Report location: appended to existing `docs/maintenance-audit.md` to avoid
  creating a new reporting structure.

### Audience And Maturity Assessment

Wait Time Canada is a public, health-adjacent observatory for emergency
department wait-time methodology, provenance, data quality, and public-health
resource context. The appropriate writing style is factual, durable, modest,
and explicit about clinical-safety and comparability limits. The repo should be
shareable with reviewers, maintainers, contributors, and public-interest
readers without sounding promotional, apologetic, private, or session-bound.

### Coverage Tier And Inventory

Coverage tier: medium, risk-based. The repository has 581 tracked files. The
professionalization inventory counted 558 reviewable text files and about
93,892 reviewable lines after excluding dependency/cache/build artifacts,
binary assets, lockfile line-by-line review, ignored local private trees, and
secret-pattern files.

Surfaces inspected:

- Top-level docs and metadata: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CHANGELOG.md`, `CITATION.cff`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
- Documentation hubs and active public docs: `docs/README.md`,
  `docs/index.md`, `docs/API.md`, `docs/openapi.yaml`,
  `docs/planning/roadmap.md`, `docs/planning/README.md`,
  `docs/planning/index.md`, `docs/development/*`,
  `docs/operations/*`, `docs/reference/*`.
- Research and stakeholder materials: `docs/geocoding-research-plan.md`,
  `docs/stakeholder-interviews/*`, `docs/research/*`,
  `docs/case-studies/ottawa-gatineau-divergence.md`.
- ADR and planning samples: `docs/adr/*`, `docs/planning/archive/*`,
  `docs/planning/implementation/archived/*`.
- Source comments and user-visible strings in representative frontend/backend
  surfaces: `frontend/components/Map.tsx`, `frontend/middleware.ts`,
  `frontend/i18n/request.ts`, selected API/page/component tests,
  `backend/src/waittime/cli/seed_sources.py`,
  `backend/src/waittime/services/benchmarking.py`, selected backend tests.
- Scripts and automation docs: `scripts/check-docs.sh`,
  `scripts/migrate-structure.sh`, `.github/ISSUE_TEMPLATE/*`,
  `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/README.md`.

### Searches And Probes Run

- `git status --short`, `git rev-parse --show-toplevel`, `git ls-files`, and a
  reviewable-file classification over tracked files.
- Filename discovery for the two required prompt-pack contract files, followed
  by read-only inspection of those files.
- Broad wording probes for chatty, apologetic, profanity, joke, temporary,
  vague TODO, and session-style language across tracked non-secret text.
- Automated-tool and non-human attribution probes, manually filtered for
  intentional docs-check fixtures, robot opt-out user-agent strings, and
  repo-local authorship guardrails.
- TODO/FIXME/HACK/XXX and temporary-wording probes across docs, source, tests,
  scripts, and workflow text.
- Personal/private-context probes across public docs and code-adjacent writing,
  manually filtered for legitimate citation authorship, ADR deciders, public
  privacy terminology, and user-facing copy.
- Emoji/status-marker probe, manually filtered for established README and CLI
  output conventions; edited only the parked Zenodo guide where the tone was
  unnecessarily celebratory.
- Manual inspection of high-signal hits rather than completing from search
  output alone.

### Candidate Wording Ledger

| Candidate | Status | Decision rationale |
| --- | --- | --- |
| Stakeholder outreach/interview scripts used avoidable first-person project rationale and scheduling language | Fixed | Templates remain usable, but wording is more durable and less personally framed. |
| `docs/geocoding-research-plan.md` presented a copied request as an ad hoc first-person prompt | Fixed | Reframed as a reusable request template without changing the hospital input list. |
| `docs/operations/zenodo-integration.md` used parked external-action wording, checkmark/status emoji, celebratory language, and a citation example typo | Fixed | DOI activation posture is unchanged; wording is calmer and citation metadata is corrected. |
| Source/test comments contained implementation-diary phrasing such as uncertainty notes and self-dialogue | Fixed | Removed or replaced with concise technical intent; no behavior or assertions changed. |
| `scripts/migrate-structure.sh` had user-directed script wording | Fixed | Output/comment now refer to this repository and required manual categorization. |
| README status icons and milestone checklist emoji | Left unchanged | They are established public presentation conventions in the repo and not misleading by themselves. |
| ADR user stories using first person | Left unchanged | User-story format is intentional architecture documentation, not personal diary language. |
| Research note saying the naloxone link-out posture applies "for now" | Left unchanged | The phrase captures a current legal/reuse posture and changing it could weaken the decision record. |
| Archived maintenance/planning history with older wording | Left unchanged | Historical context is useful; no active doc points to it as current behavior. |
| Docs-check tests and guardrails containing automated-tool names | Left unchanged | They are intentional negative fixtures and policy checks, not attribution. |
| Exact private prompt-pack path | Omitted from report | Public documentation boundary forbids local environment-specific paths. |

### Safe Changes Made

- Rewrote stakeholder templates to describe the project and interview purpose
  neutrally while preserving the workflow.
- Reframed the geocoding research prompt as a reusable request template.
- Cleaned the Zenodo guide by replacing transient approval wording, removing
  decorative status markers, reducing second-person claims, and fixing the
  `family-names` example.
- Replaced frontend/backend source and test comment residue with concise
  technical comments or removed comments that added no durable value.
- Removed a stale E2E comment claiming `ThemeToggle` had not been added even
  though `frontend/components/Header.tsx` now renders it.
- Appended this addendum to the existing audit report.
- Updated `docs/planning/roadmap.md` with a narrow status/follow-up note for
  the professionalization pass.

### Rewrite Patterns Applied

- Personal rationale to project rationale.
- Prompt/session wording to reusable template wording.
- Self-dialogue test comments to technical assertions or no comment.
- Celebration and owner-specific wording to neutral operational wording.
- Stale planning note to deletion when the code already disproved it.

### Verification

Passed:

- `bash scripts/check-docs.sh`
- `cd backend && <local-uv> run ruff check src tests scripts`
- `cd backend && <local-uv> run ruff format --check src tests scripts`
- `cd backend && TMPDIR=/tmp TMP=/tmp TEMP=/tmp <local-uv> run pytest tests/unit/test_benchmarking_coverage.py tests/unit/services/test_benchmarking_safety.py tests/unit/test_source_consistency.py`
  - Result: 16 passed.
- `cd frontend && PATH=<node22-bin>:$PATH npm run lint`
- `cd frontend && PATH=<node22-bin>:$PATH npm run type-check`
- `cd frontend && PATH=<node22-bin>:$PATH npm run type-check:test`
- `cd frontend && PATH=<node22-bin>:$PATH npm run test:unit -- tests/components/HospitalList.test.tsx app/api/compare/route.test.ts tests/api/hospitals.test.ts`
  - Result: 3 test files passed, 15 tests passed.
- `cd frontend && PATH=<node22-bin>:$PATH npm run format:check`
- `git diff --check`

Initial direct `uv` and `npm` invocations failed because those executables were
not on `PATH` in this shell. Verification was rerun with explicit existing local
tool paths, redacted here to preserve the public documentation boundary, and
the frontend's Node 22 runtime.

### Risks, Assumptions, And Follow-Ups

- No secret files, ignored private trees, production systems, deploys, or
  production data were inspected or touched.
- The pass did not mass-rewrite README/ADR emoji/status conventions because
  that would create broad style churn without clear value.
- The pass did not rewrite archived planning documents except where searches
  were needed to classify false positives.
- Full backend and frontend suites were not rerun because edits were limited to
  docs and comments; targeted checks plus lint/type/docs verification covered
  the changed surfaces.
- A future focused pass could review old historical scripts such as
  `scripts/migrate-structure.sh` for continued usefulness, but that would be a
  maintenance/ownership decision rather than a wording-only change.
