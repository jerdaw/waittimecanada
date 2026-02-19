# Milestone 21: Internationalization (French Support)

**Status:** In Progress
**Version:** 1.0.0
**Owner:** Automated Agent
**Date:** 2026-02-16

## Executive Summary

This milestone implements full French language support (i18n) for Wait Time Canada, addressing the "High-Value Expansion" priority in the roadmap. Given our coverage of Quebec (380+ hospitals) and the bilingual nature of Canadian healthcare, this is a critical step for "Adoption" and "Health Advocate" competencies.

We will use `next-intl` for routing and content management, establishing a `/fr` sub-path strategy while maintaining `/` (English) as the default. This ensures SEO best practices with `hreflang` tags and minimal friction for existing users.

## Current State & Assumptions

- **Architecture:** Next.js 14 App Router.
- **Content:** Currently hardcoded English strings in components and pages.
- **Data:** Database content (hospital names) is mixed/English. API responses are English-keyed.
- **Quebec Specifics:** We already have specific handling for Quebec (occupancy), making French support particularly relevant.
- **Assumption:** We will NOT translate the database content (hospital names) in this pass. We will focus on the *Application UI* (Chrome, Menus, Methodology Warnings, Disclaimers).

## Goals & Deliverables

1.  **Infrastructure:** Install and configure `next-intl` with middleware for locale detection and routing.
2.  **Content Extraction:** Extract all hardcoded UI strings into dictionary files (`en.json`, `fr.json`).
3.  **Component Updates:** Refactor Client and Server Components to consume translations.
4.  **Quebec Localization:** Ensure specific Quebec terminology ("Occupancy" vs "Taux d'occupation", "Registration" vs "Inscription") is medically accurate.
5.  **SEO:** Implement `hreflang` alternates and localized metadata.

## Phased Implementation Plan

### Phase 1: Infrastructure & Routing (Core)
**Goal:** Enable `/fr` routes and locale detection without breaking the existing app.

- [ ] **Install Dependencies:** `npm install next-intl`
- [ ] **Configure Middleware:** Create `src/middleware.ts` (or update existing) to handle `/(fr|en)/` routing.
- [ ] **Update Next Config:** Configure `next.config.mjs` with `next-intl` plugin.
- [ ] **Directory Restructure:** Move `app/[...rest]` pages into `app/[locale]/`.
    - *Risk:* High churn. Need to carefully move `page.tsx`, `layout.tsx` etc.
- [ ] **Verification:** Manual check of `localhost:3000/fr` rendering a basic translated string.

### Phase 2: Content Extraction (The "Grunt Work")
**Goal:** Move hardcoded strings to JSON dictionaries.

- [ ] **Create Dictionaries:** `messages/en.json` and `messages/fr.json`.
- [ ] **Global UI:** Translate Navbar, Footer, 911 Banner, Emergency Disclaimer.
- [ ] **Home Page:** Translate Hero text, Search placeholders, Filter options.
- [ ] **Methodology Components:** Translate `MethodologyWarning`, `OccupancyBadge` tooltips.
    - *Key Terminology:*
    - "Wait Time" -> "Temps d'attente"
    - "Stretcher Occupancy" -> "Taux d'occupation des civières"
    - "Registration" -> "Inscription"
    - "Triage" -> "Triage"

### Phase 3: Dynamic & Metadata
**Goal:** Localize items that affect SEO and data presentation.

- [ ] **Metadata:** Update `generateMetadata` in `layout.tsx` to use localized titles/descriptions.
- [ ] **Sitemap:** Update `sitemap.ts` to include alternate links.
- [ ] **Date Formatting:** Use `Intl.DateTimeFormat` or `date-fns` locale for "Last updated" timestamps.
- [ ] **Number Formatting:** Ensure percentages use comma decimals for French (e.g., "110,5 %").

### Phase 4: Verification & Polish
**Goal:** Ensure quality and absence of regressions.

- [ ] **Automated Tests:** Update Playwright E2E tests to check `/en` and `/fr` routes.
- [ ] **Unit Tests:** Fix any broken component tests due to `intl` provider mocking.
- [ ] **Language Switcher:** Add a polished toggle (EN/FR) in the Navbar.

## Timeline

| Phase | Duration | Dependency |
|-------|----------|------------|
| 1. Infrastructure | 1 Day | None |
| 2. Extraction | 2-3 Days | Phase 1 |
| 3. Dynamic/SEO | 1 Day | Phase 2 |
| 4. Verification | 1 Day | Phase 3 |

**Total:** ~1 Week

## Rollout & Rollback

- **Rollout:** Merge to `main`. The feature is additive (new routes).
- **Rollback:** Revert middleware changes and move `app/[locale]` back to root if catastrophic routing failure occurs.

## Key Risks

- **Route Conflicts:** Existing API routes must NOT be captured by the `[locale]` middleware.
    - *Mitigation:* Explicit `matcher` exclusions in middleware.
- **Performance:** larger bundle size with translation files.
    - *Mitigation:* Server-side translation where possible to reduce client bundle.

## Validation Strategy

### Automated Verification
Run the new E2E test suite:
```bash
npm run test:e2e
```
This will include new tests specifically checking:
1.  Visiting `/fr` shows "Temps d'attente".
2.  Clicking "EN" switches back to `/`.

### Manual Verification
1.  Navigate to `http://localhost:3000/fr/hospitals`.
2.  Verify the "911" banner is translated.
3.  Check a specific Quebec hospital card. Verify "Stretcher Occupancy" displays as "Taux d'occupation".
4.  Verify API requests still work (no 404s).
