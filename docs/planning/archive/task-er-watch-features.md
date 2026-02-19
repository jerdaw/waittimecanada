# ER Watch Feature Implementation Task List (Completed Feb 4, 2026)

> Archived task plan (historical reference). Items fully delivered.

## Phase 1: Critical Safety & Quick Wins
- [x] Add 911 Emergency Banner component
- [x] Configure Tailwind dark mode support
- [x] Install next-themes for theme management
- [x] Add theme toggle to layout
- [x] Update globals.css with dark mode color scheme

## Phase 2: Core UX Features

### Split View Layout
- [x] Create HospitalList component with compact cards
- [x] Create ViewToggle component (List | Map | Split)
- [x] Refactor page.tsx layout for view modes
- [x] Add list/map synchronization (hover/select states)
- [x] Mobile responsive layout (stacked vs side-by-side)

### Wait Time Trend Charts
- [x] Create backend API: GET /api/hospitals/[slug]/trends
- [x] Create TrendChart component with Recharts
- [x] Add timeframe toggles (24h | 7d | 30d)
- [x] Create hospital detail modal/page (Integrated into Hospital Popup)
- [x] Write unit tests for trend API and component

## Phase 3: Polish & Engagement
- [x] Create Hero section component
- [x] Add live preview card with nearest/shortest stats
- [x] Add smooth animations and transitions
- [x] Create expandable hospital card accordion

## Phase 4: Progressive Enhancement
- [x] Add PWA manifest.json
- [x] Create service worker for offline capability
- [x] Add install prompt logic
- [x] Create Apple touch icons

## Testing & Verification
- [x] Unit tests for all new components (Phase 1)
- [x] E2E tests for view toggle functionality (Phase 1)
- [x] E2E tests for dark mode persistence (Phase 1)
- [x] Unit tests for Split View components (Phase 2)
- [x] E2E tests for Split View functionality (Phase 2)
- [x] Unit/Integration tests for Trend Charts (Phase 2)
- [x] Unit tests for Hero Section (Phase 3)
- [x] E2E tests for Hero flow (Phase 3)
- [x] Verify PWA installability
