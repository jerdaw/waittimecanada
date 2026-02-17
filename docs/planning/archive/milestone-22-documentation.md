# Milestone 22: Portfolio Documentation & Project Polish

**Goal:** Finalize "Scholar" and "Professional" artifacts for medical school admissions portfolio, ensuring all documentation is deployed, standardized, and verifiable.

## User Review Required

> [!NOTE]
> This milestone focuses on "Portfolio Polish" rather than new features. It addresses discrepancies between the `roadmap.md` and the actual state of the repository (e.g., Zenodo integration, Mermaid diagrams).

## Proposed Changes

### Documentation (Scholar/Professional)

#### [NEW] `docs/openapi.yaml`
- Create a standard OpenAPI 3.0 specification file mirroring the contracts in `docs/API.md`.
- **Why:** "Scholar" competency; standardizes the research API for external review.

#### [NEW] `.github/workflows/deploy-docs.yml`
- Create a GitHub Action to build and deploy MkDocs to GitHub Pages.
- **Trigger:** Push to `main` (paths: `docs/**`, `mkdocs.yml`).
- **Why:** "Professional" competency; live documentation site.

#### [MODIFY] `mkdocs.yml`
- Update configuration to ensure strict build and correct repository links.
- Add `openapi` plugin/reference if applicable (or just link to the raw YAML).

#### [MODIFY] `README.md`
- Update badges to be dynamic where possible (or ensure links are correct).
- Verify Zenodo badge points to the valid record.

### Roadmap Reconciliation

#### [MODIFY] `docs/planning/roadmap.md`
- specific updates to mark "Zenodo integration", "Architecture diagram", and "M20/M21" items as complete.
- Remove duplicate entries in "Next" section.

### Operational Polish

#### [NEW] `backend/scripts/generate_freshness_badge.py`
- Python script to query the database and generate a JSON file compatible with shields.io (schemaVersion 1).
- Content: `{"schemaVersion": 1, "label": "Last Scrape", "message": "<time_ago>", "color": "green"}`.
- **Why:** "Systems" engineering; proves the data is live even if the frontend is offline.

#### [MODIFY] `.github/workflows/scraper-cron.yml`
- Add step to run `generate_freshness_badge.py` and upload the result to a Gist (via secret) or commit to an orphan branch.
- *Constraint:* Requires `GIST_SECRET` or permissions. Will use "commit to `badges` branch" approach if allowed, otherwise will just log it for now.

## Verification Plan

### Automated Tests
- **Docs Build:** `mkdocs build --strict` must pass.
- **OpenAPI Validation:** Use a linter (e.g., `vacuum` or online validator) to ensure `openapi.yaml` is valid.
- **Badge Generation:** Run `python backend/scripts/generate_freshness_badge.py` and verify JSON output.

### Manual Verification
1.  **Docs Site:** Verify `https://jerdaw.github.io/waittimecanada/` loads after merge.
2.  **Badges:** Verify README badges render correctly.
3.  **Roadmap:** Visually inspect `docs/planning/roadmap.md` for correctness.
