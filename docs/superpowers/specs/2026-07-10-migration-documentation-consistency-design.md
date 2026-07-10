# Migration Documentation Consistency Design

**Date:** 2026-07-10

**Status:** Approved for implementation planning

## Context

`backend/migrations/README.md` is the canonical human-readable migration
history, while `backend/scripts/check_migration_sequence.py` enforces migration
filename and prefix rules in CI. The two surfaces have drifted:

- the README says there are 21 executable migrations, but 22 `*.sql` files
  currently execute;
- it says the next prefix is `022`, although migration `022` exists and `023`
  is next;
- examples still use `022` for a new migration;
- migrations `014`, `015`, `018`, `019`, and
  `020_add_public_health_system_metrics.sql` do not have history headings;
- the `005_create_functions.sql` entry contains an unresolved content
  placeholder; and
- later migration entries appear before `005`, so the history is not
  chronological.

The filename guard cannot detect any of these documentation defects. A focused
follow-up should reconcile the README and make the existing guard validate the
small set of facts that can be derived reliably from the files on disk.

## Goals

1. Make the migration README accurately describe every current executable and
   intentionally skipped migration.
2. Make its executable count, next prefix, examples, and history order accurate.
3. Replace the `005` placeholder with the functions and triggers defined by the
   migration.
4. Extend the existing CI guard so future migration additions cannot silently
   omit a history entry or leave the canonical count and next-prefix statement
   stale.
5. Preserve applied migration files, migration execution behavior, and the
   historical duplicate-`020` exception.

## Non-Goals

- Editing any existing SQL migration.
- Creating or applying a database migration.
- Generating the prose README from SQL files.
- Validating every explanatory claim in the README from SQL syntax.
- Redesigning the migration runner or its checksum ledger.
- Resolving the separate Ontario methodology and ontology decision.

## Approaches Considered

### 1. Extend the existing sequence checker (selected)

Add a separate documentation-validation function to
`check_migration_sequence.py` and call it from the existing command. This keeps
all disk-derived migration invariants behind the command already run by CI and
contributors.

This is the smallest approach with durable prevention. The sequence-only
function remains independently callable so current tests and consumers retain
their narrow contract.

### 2. Add a separate migration-documentation checker

A new script would separate filename and documentation concerns, but it would
add another command, test module, and CI integration point for a small set of
closely related invariants.

### 3. Generate the README

Generation would prevent inventory drift, but it would constrain useful prose,
milestone context, rationale, and rollback notes. It is disproportionate to the
current defect.

## Design

### README Reconciliation

Update `backend/migrations/README.md` so it has:

- `Found 22 migration files:` in the quick-start output;
- current ranges ending in `022` where the text describes execution order;
- the canonical sentence ``The next migration number is `023`.``;
- new-migration examples using `023`;
- one exact level-four heading for every `*.sql` and `*.sql.skip` file;
- chronological history ordering, including both preserved `020` entries;
- concise entries for migrations `014`, `015`, `018`, `019`, and
  `020_add_public_health_system_metrics.sql`; and
- the actual functions and triggers from `005_create_functions.sql` instead of
  the unresolved placeholder.

The new entries will summarize only facts present in the SQL files and relevant
maintained architecture or ADR documentation. They will not invent production
application dates, deployment claims, or rollback results.

### Documentation Validator

Keep `validate_migrations()` focused on names, missing prefixes, and duplicate
prefixes. Add a sibling function with a narrow contract:

```python
def validate_migration_documentation(
    migrations_dir: Path = MIGRATIONS_DIR,
    readme_path: Path = MIGRATIONS_README,
) -> list[str]:
    """Return disk-derived migration README consistency errors."""
```

The function will read the README as UTF-8 and validate four invariant groups.

#### 1. Inventory headings

Parse exact level-four migration headings rather than searching for filenames
anywhere in prose or examples. Every file returned by `migration_files()` must
have exactly one heading, and every parsed migration heading must correspond to
a file on disk. This detects missing, duplicate, and stale history entries.

Both executable `*.sql` files and intentionally skipped `*.sql.skip` files are
part of the documented inventory.

#### 2. Executable count

Count files ending in `.sql`, excluding `.sql.skip`, to match
`run_migrations.py`. Compare that value with the canonical quick-start line:

```text
Found N migration files:
```

The validator will report a missing or mismatched count explicitly.

#### 3. Next prefix

Take the maximum numeric prefix across executable and skipped migration files,
then add one. Duplicate prefix `020` therefore has no special effect on the
calculation. Compare the result with the single canonical statement:

```text
The next migration number is `NNN`.
```

The validator will report a missing, duplicate, or stale statement.

#### 4. Unresolved placeholders

Reject whole-word `TODO` or `TBD` placeholders in the canonical migration
README and include the line number in the error. Markdown task-list checkboxes
are not placeholders and remain valid.

### Command Behavior and Errors

`main()` will aggregate filename-sequence and README errors and return nonzero
when either group fails. It will print one concise heading followed by
actionable bullet errors. Existing `validate_migrations()` callers will not
implicitly run documentation validation.

A missing or unreadable README will be returned as a validation error rather
than producing an unhandled traceback. No files will be modified by the guard.

### CI and Contributor Flow

The repository already runs the sequence checker in Scraper CI, so no workflow
change is required. Contributors continue to run:

```bash
cd backend
uv run python scripts/check_migration_sequence.py
```

The command will now validate both migration filenames and the canonical
migration README.

## Testing Strategy

Implementation will follow test-driven development in
`backend/tests/unit/test_check_migration_sequence.py`.

Focused tests will cover:

1. the real repository passes both filename and README validation;
2. a complete synthetic README passes;
3. a missing migration heading is rejected;
4. a heading for a nonexistent migration is rejected;
5. duplicate headings are rejected;
6. a stale executable count is rejected;
7. a stale or duplicate next-prefix statement is rejected;
8. a `TODO` or `TBD` placeholder reports its line; and
9. a missing README produces an actionable validation error.

Existing sequence tests will remain unchanged except where command-level output
must reflect the broader validation heading.

Verification will include the focused unit module, the checker command, backend
format/lint/type/test gates in proportion to the change, and documentation
quality checks. CI results will be treated as authoritative for any local lane
that cannot run because of environment prerequisites.

## Documentation and Completion Record

The implementation plan will record exact commands and results. The maintenance
audit will receive a concise completion note so the original drift is not
selected again. Removing the explicit `005` placeholder and adding the guard
will make the canonical documentation gap complete.

## Branch and Delivery Boundaries

The work lives on `codex/migration-docs-consistency`, independently of open PR
#83. It will be delivered as a ready, reviewable PR but will not be merged
without explicit authorization because changes under `docs/` trigger the
repository's documentation deployment workflow on `main`.

No deployment, database operation, release, secret change, or production write
is part of this design.
