# Project Maintenance & Cleanup Plan

This plan follows the established `roadmap-process.md` and `documentation-guidelines.md` to finalize the recent test stabilization work and perform general repository maintenance.

## Proposed Changes

### 1. Cleanup & Archiving
- **[MOVE]** `docs/planning/implementation/milestone-19-governance-quality.md` to `docs/planning/archive/` (marking as Delivered/Closed in roadmap).
- **[ARCHIVE]** Current stabilization implementation plan (transferring key findings to roadmap).
- **[CLEANUP]** Verify no leftover `test-results` or `npm-debug.log` files outside of ignored dirs.

### 2. Roadmap & Documentation
- **[MODIFY]** `docs/planning/roadmap.md`:
  - Update "Current Status" with M19 completion and Test Stabilization.
  - Add "Desktop Test Suite Stabilization" to "Completed Milestones".
  - Mark item #44 (Mobile-responsive testing) as Complete.
  - Check off relevant M19 items.
- **[NEW]** ADR for Map Loading & Z-Index Strategy (if not already covered).

### 3. Agent Configuration & Attribution
- **[NEW]** Create `GEMINI.md` as a symlink to `AGENTS.md`.
- **[MODIFY]** Verify `AGENTS.md` (and thus `CLAUDE.md`/`GEMINI.md`) has explicit "Human Authorship Only" section.
- **[AUDIT]** Scan codebase for AI/Agent attribution in comments, logs, or commits.

### 4. Verification Matrix
- **Backend**:
  - `ruff check backend/src backend/tests`
  - `mypy backend/src`
  - `python -m pytest backend/tests -m unit`
- **Frontend**:
  - `npm run lint`
  - `npm run type-check`
  - `npm run test:unit`

### 5. Git Operations
- **[AUDIT]** Check for secrets using `grep` patterns.
- **[COMMIT]** Commit changes with conventional commit messages.
- **[PUSH]** Push to remote and verify human author listing.

## Verification Plan

### Automated Tests
- Full `npm run build` to ensure no environment regressions.
- Backend unit and integration tests.
- Frontend unit tests.

### Manual Verification
- Verify `GEMINI.md` symlink.
- Inspect `roadmap.md` rendering.
