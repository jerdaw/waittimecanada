
# E2E Tests
test-e2e: ## Run end-to-end pipeline tests
	cd backend && TMPDIR=/tmp TMP=/tmp TEMP=/tmp uv run pytest tests/e2e/test_pipeline.py

test-visual: ## Run visual regression tests
	cd frontend && npx playwright test tests/e2e/visual.spec.ts

test-visual-update: ## Run visual regression tests and update snapshots
	cd frontend && npx playwright test tests/e2e/visual.spec.ts --update-snapshots
