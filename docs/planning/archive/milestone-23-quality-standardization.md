# implementation_plan.md

# Milestone 23: Quality & Standardization

This milestone focuses on hardening the application's quality assurance through automated accessibility testing, mobile responsiveness verification, and enforcing strict type safety across the full stack.

## User Review Required

> [!IMPORTANT]
> **New Dependency**: We will be adding `@axe-core/playwright` to the frontend devDependencies for automated accessibility testing.

## Proposed Changes

### Frontend Quality

#### [NEW] Accessibility Testing
- Install `@axe-core/playwright`.
- Create `frontend/tests/e2e/accessibility.spec.ts`.
- Implement automated checks for:
  - Landing page
  - Map view (with and without hospital selected)
  - List view
  - About/Methods pages
- **Goal**: Ensure no critical a11y violations (WCAG 2.1 AA target).

#### [MODIFY] Mobile Responsiveness
- Review `frontend/tests/e2e/mobile.spec.ts`.
- [Refactor] Standardize viewport sizes to match common devices (iPhone 12/14, Pixel 5).
- [Feature] Add test case for the "Quick Actions" drawer on mobile.
- [Feature] Add test case for the "Access Burden Estimator" expansion on mobile.

#### [AUDIT] TypeScript Strict Mode
- Audit codebase for `any`, `@ts-ignore`, and `@ts-expect-error`.
- Remove manual suppressions where possible.
- Ensure `tsconfig.json` remains in `strict: true`.

### Backend Quality

#### [MODIFY] Mypy Strict Mode
- Update `backend/pyproject.toml` to increase strictness:
  - Set `disallow_untyped_calls = true`
  - Set `disallow_untyped_decorators = true`
- Fix resulting type errors in `src/`.
- If external library stubs are missing, add specific overrides in `pyproject.toml` rather than global looseness.

## Verification Plan

### Automated Tests
- **Frontend Accessibility**: `npm run test:e2e -- tests/e2e/accessibility.spec.ts`
- **Frontend Mobile**: `npm run test:e2e -- tests/e2e/mobile.spec.ts`
- **Backend Typing**: `cd backend && .venv/bin/python -m mypy src`
- **Frontend Typing**: `cd frontend && npm run type-check`

### Manual Verification
- **Accessibility**: specific manual check of tab navigation on the Map View to ensure keyboard usability.
