# Home Page Premium UX Improvement Plan

**Created:** 2026-02-24
**Based on:** HOME_ANALYSIS.md (2026-02-24)
**Branch:** `ui/premium-ux-upgrade`

---

## Component Strategy

**Principle:** Reuse first. No new component files unless the abstraction is clearly justified.

| Decision                            | Rationale                                                                                                                              |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| No new shared Button component      | Would be ideal long-term but adding a design-system primitive for one page is premature. Fix individual button inconsistencies inline. |
| No new shared Card component        | Same reasoning. Keep ad-hoc Tailwind patterns consistent by example.                                                                   |
| Modify existing components in-place | Hero, Header, Footer, page.tsx all get refined rather than replaced.                                                                   |
| Remove or inline HeroStats          | Consolidate trust signals. May fold cadence note into badge or description.                                                            |
| Keep ProvinceCoverage as-is         | Strong trust signal with official source names.                                                                                        |

---

## Design-System Alignment Notes

- All changes must use existing CSS variable tokens (`--primary`, `--muted`, `--border`, etc.)
- All spacing uses Tailwind's standard scale (no arbitrary pixel values unless matching existing patterns)
- All new text must go through `useTranslations()` — both EN and FR
- Dark mode parity: every visual change must work in both light and dark themes
- Motion: all new animations must respect `prefers-reduced-motion: reduce`

---

## Phase 1 — Quick Wins (High Impact, Low Effort)

### 1.1 Fix Double Footer

- [ ] **Remove `<Footer />` from `page.tsx`**
- **Why:** `layout.tsx:78` already renders `<Footer />` globally. The homepage renders it again at line 455-457, causing duplicate footers after hero dismiss.
- **Implementation:** Delete the `{!showHero && <Footer />}` block from `page.tsx`. The layout footer handles all pages.
- **Taste guidance:** N/A — pure bug fix.
- **Impact:** High | **Effort:** Low | **Stream:** UI

### 1.2 Fix Badge "Real-Time" Contradiction

- [ ] **Change badge text from "Real-Time Canadian ER Data" to "Canadian ER Wait Time Data"**
- **Why:** "Real-Time" contradicts "Updated Every 4 Hours" in the stats bar. This undermines trust. The data is authoritative but not real-time.
- **Before:** `"Real-Time Canadian ER Data"`
- **After:** `"Canadian ER Wait Time Data"` (EN) / `"Données sur les temps d'attente aux urgences canadiennes"` (FR)
- **Taste guidance:** Honest, specific, professional. Avoid marketing language that overreaches.
- **Impact:** High | **Effort:** Low | **Stream:** Copy

### 1.3 Fix Featured Card LIVE Accuracy

- [ ] **Only show "LIVE" badge when `last_updated` is within the last 60 minutes. Otherwise show relative time.**
- **Why:** "LIVE" is misleading when data is hours old. This is an accuracy/trust issue.
- **Implementation:** In `Hero.tsx`, check `featuredHospital.hospital.last_updated`. If within 60 min, show "LIVE". Otherwise show "Updated Xh ago" using `date-fns` `formatDistanceToNow`.
- **Before:** Always shows "LIVE"
- **After:** "LIVE" (if recent) or "Updated 2h ago" (if stale)
- **Taste guidance:** Subtle badge color change: green for live, muted for stale.
- **Impact:** High | **Effort:** Low | **Stream:** Component
- **Dependencies:** New translation keys for stale state.

### 1.4 Add `prefers-reduced-motion` Support

- [ ] **Add a global CSS rule to disable animations for users who prefer reduced motion**
- **Why:** Accessibility requirement. All `animate-in`, `animate-ping`, hover transforms currently play unconditionally.
- **Implementation:** Add `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; } }` to `globals.css`.
- **Taste guidance:** Invisible to most users. Critical for accessibility.
- **Impact:** High | **Effort:** Low | **Stream:** QA/A11y

### 1.5 Replace `dangerouslySetInnerHTML` in Mobile Hint

- [ ] **Use `t.rich()` instead of `dangerouslySetInnerHTML` for the mobile hint**
- **Why:** `dangerouslySetInnerHTML` bypasses React's XSS protection. The `t.rich()` pattern is already used elsewhere in the codebase (AboutSection).
- **Before:** `<p ... dangerouslySetInnerHTML={{ __html: t.raw('mobileHint') }} />`
- **After:** `<p ...>{t.rich('mobileHint', { strong: (chunks) => <strong>{chunks}</strong> })}</p>`
- **i18n change:** Update `mobileHint` value to use `<strong>` tag format compatible with `t.rich()`.
- **Impact:** Medium | **Effort:** Low | **Stream:** Component

### 1.6 Add Focus-Visible Rings to Province Pills

- [ ] **Add `focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2` to province pill buttons**
- **Why:** Keyboard users cannot see which province pill is focused. `aria-pressed` exists but visual feedback is missing.
- **Implementation:** Add Tailwind focus-visible classes to the pill button `className` in `Hero.tsx`.
- **Taste guidance:** Use `ring-primary/40` to match existing subtle accent patterns. Not heavy outline.
- **Impact:** Medium | **Effort:** Low | **Stream:** A11y

---

## Phase 2 — Core UX/Content Improvements (High Impact, Medium Effort)

### 2.1 Simplify Hero Vertical Stack

- [ ] **Consolidate 8 hero elements into 5-6 with clear hierarchy**
- **Why:** Badge + HeroStats + H1 + description + province pills + CTAs + ProvinceCoverage + HeroHowItWorks all have similar visual weight. The hero feels dense rather than premium.
- **Implementation:**
  1. Remove HeroStats component from hero. Fold the "Updated Every 4 Hours" cadence note into a smaller line under the description or into the badge itself.
  2. Keep province pills (interactive, unique function).
  3. Keep ProvinceCoverage strip (trust signal with official source names).
  4. Move HeroHowItWorks out of the hero entirely — position it as a subtle section that appears after hero dismiss (alongside AccessInsights), or remove it from the homepage and rely on the FAQ page.
  5. Increase spacing between remaining elements: `space-y-6` → `space-y-8` for the main stack.
- **Visual hierarchy after change:** Badge → H1 → Description + cadence → Province pills → CTAs → ProvinceCoverage
- **Taste guidance:** Fewer elements = more breathing room = more premium. Each element should feel intentional, not crammed.
- **Impact:** High | **Effort:** Medium | **Stream:** UI/Component

### 2.2 Improve Hero Spacing & Rhythm

- [ ] **Increase whitespace in hero section, use consistent vertical rhythm**
- **Why:** Current `space-y-6` creates a tight stack. Premium design needs breathing room.
- **Implementation:**
  - Hero section: `py-8 md:py-12 lg:py-14` → `py-12 md:py-16 lg:py-20`
  - Content stack: `space-y-6` → `space-y-8`
  - Gap between left content and featured card: `gap-12 lg:gap-20` → `gap-12 lg:gap-16` (slightly tighter — the card should feel connected, not floating away)
- **Taste guidance:** Generous padding is the single most effective premium signal. Don't be afraid of whitespace.
- **Impact:** High | **Effort:** Low | **Stream:** Styling

### 2.3 Tighten Header Nav & Mobile

- [ ] **Add minimal mobile navigation (hamburger → slide-down sheet with nav links)**
- **Why:** Desktop nav (`hidden md:flex`) is completely inaccessible on mobile. Users on mobile cannot reach /data-quality, /analytics, /methods, /faq from the header.
- **Implementation:** Add a hamburger button visible on `md:hidden`. On click, toggle a slide-down panel below header with nav links. Use existing nav link styling. No new dependencies.
- **Taste guidance:** Keep it minimal — just the 4 nav links + theme toggle. No full-screen overlay. A simple dropdown panel.
- **Impact:** High | **Effort:** Medium | **Stream:** Component
- **Dependencies:** New translation key for mobile menu aria-label.

### 2.4 Improve Post-Hero Transition

- [ ] **Add subtle section dividers and stagger animations when hero is dismissed**
- **Why:** After hero dismiss, AccessInsightsSummary + RegionDashboard + split view all appear at once with no visual rhythm.
- **Implementation:**
  - Add `animate-in fade-in slide-in-from-bottom-4 duration-500` to the AccessInsightsSummary wrapper (already has `animate-in fade-in duration-500` — add the slide).
  - Stagger: insights section at `delay-0`, split view at `delay-150`.
  - Add subtle `border-b border-border/30` between insights section and split view.
- **Taste guidance:** Subtle stagger gives a feeling of intentionality. Don't over-animate.
- **Impact:** Medium | **Effort:** Low | **Stream:** Motion

---

## Phase 3 — Structural/Advanced Enhancements (Medium Impact, Higher Effort)

### 3.1 Improve AboutSection Visual Weight

- [ ] **Reduce visual prominence of AboutSection — it should feel like an aside, not a main section**
- **Why:** Currently `py-12 bg-card border-b` gives it the same weight as content sections. For a portfolio project, the "about" matters but shouldn't compete with the data.
- **Implementation:**
  - Reduce padding: `py-12` → `py-8`
  - Softer background: `bg-card` → `bg-muted/20` or just `bg-background`
  - Smaller title: `text-2xl` → `text-xl`
  - Start collapsed by default: `useState(true)` → `useState(false)` — let users opt in to reading the bio.
- **Taste guidance:** The bio should be discoverable but not imposing. Collapsed-by-default signals confidence.
- **Impact:** Medium | **Effort:** Low | **Stream:** UI

### 3.2 Replace Hero Inline SVGs with Lucide Icons

- [ ] **Use Lucide's `ArrowRight` and `ChevronRight` instead of inline SVG in Hero CTAs**
- **Why:** Consistency with the rest of the codebase. Reduces JSX verbosity. Matches icons used in HeroHowItWorks.
- **Implementation:** Import `ArrowRight`, `ChevronRight` from `lucide-react`. Replace inline `<svg>` in explore button and methods link.
- **Taste guidance:** No visual change — purely a consistency/maintenance improvement.
- **Impact:** Low | **Effort:** Low | **Stream:** Component

### 3.3 Soften Badge Animation

- [ ] **Replace `animate-ping` on badge dot with `pulse-soft`**
- **Why:** Two `animate-ping` elements on screen (badge + LIVE) compete for attention. The badge ping is the less important one.
- **Implementation:** In `Hero.tsx`, change badge dot from `animate-ping` to `animate-pulse-soft` (custom animation already in Tailwind config).
- **Taste guidance:** One pinging element is acceptable. Two is noisy.
- **Impact:** Low | **Effort:** Low | **Stream:** Motion

### 3.4 Add `aria-label` / Accessible Name to Header Search

- [ ] **Add `aria-label` to the header search input**
- **Why:** The search input relies on `placeholder` for its accessible name. Screen readers may not announce placeholders consistently.
- **Implementation:** Add `aria-label={t('searchLabel')}` to both desktop and mobile search inputs.
- **i18n:** New key `Header.searchLabel` = "Search hospitals by name or city"
- **Impact:** Medium | **Effort:** Low | **Stream:** A11y

---

## Phase 4 — Polish/QA/Optimization

### 4.1 Dark Mode Visual Audit

- [ ] **Verify all modified components render correctly in dark mode**
- **Why:** CSS variables handle most cases, but hover states, border colors, and animation overlays may need tweaking.
- **Implementation:** Manual review. Check hero gradients, badge colors, province pills, mobile nav, AboutSection.
- **Impact:** Medium | **Effort:** Low | **Stream:** QA

### 4.2 Review Other Pages for Double Footer

- [ ] **Check if analytics, data-quality, methods, faq pages also render their own `<Footer />`**
- **Why:** If layout.tsx renders Footer globally, no page should render its own Footer. This is a broader consistency issue.
- **Implementation:** Audit all page files. Remove redundant `<Footer />` renders.
- **Impact:** Medium | **Effort:** Low | **Stream:** QA

### 4.3 Verify Mobile Touch Targets

- [ ] **Ensure all interactive elements meet 44x44px minimum touch target**
- **Why:** Province pills, nav links, and search clear button may be borderline.
- **Implementation:** Audit with dev tools. Increase padding if needed.
- **Impact:** Low | **Effort:** Low | **Stream:** A11y/Mobile

### 4.4 TypeScript/Lint/Build Verification

- [ ] **Run `npm run build`, `npm run lint`, `npm run test -- --run`**
- **Why:** No regressions.
- **Implementation:** CLI checks.
- **Impact:** High | **Effort:** Low | **Stream:** QA

---

## i18n Changes Required

| Key                           | EN                                                            | FR                                                                              | Reason                                                               |
| ----------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `Hero.badge`                  | "Canadian ER Wait Time Data"                                  | "Données sur les temps d'attente aux urgences canadiennes"                      | Fix "Real-Time" contradiction                                        |
| `Hero.card.stale`             | "Updated {time}"                                              | "Mis à jour {time}"                                                             | Stale data card label                                                |
| `Hero.card.staleTime.hours`   | "{count}h ago"                                                | "il y a {count}h"                                                               | Relative time for stale card                                         |
| `Hero.card.staleTime.minutes` | "{count}m ago"                                                | "il y a {count}m"                                                               | Relative time for stale card                                         |
| `Header.searchLabel`          | "Search hospitals by name or city"                            | "Rechercher des hôpitaux par nom ou ville"                                      | Accessible search label                                              |
| `Header.mobileMenu`           | "Menu"                                                        | "Menu"                                                                          | Mobile nav button                                                    |
| `Header.mobileMenuClose`      | "Close menu"                                                  | "Fermer le menu"                                                                | Mobile nav close                                                     |
| `HomePage.mobileHint`         | "Tap <strong>List</strong> in the header to browse hospitals" | "Appuyez sur <strong>Liste</strong> dans l'en-tête pour parcourir les hôpitaux" | Updated for t.rich() format (no change to value, just usage pattern) |

---

## a11y Checklist

- [ ] `prefers-reduced-motion` global rule added
- [ ] Province pills have `focus-visible` ring
- [ ] Header search has `aria-label`
- [ ] Mobile nav hamburger has `aria-expanded` and `aria-label`
- [ ] All decorative SVGs have `aria-hidden="true"`
- [ ] No `dangerouslySetInnerHTML` remaining on homepage
- [ ] Color contrast verified in both light and dark themes

---

## Performance Considerations

- No new dependencies added
- No new client components — all changes are to existing `"use client"` components
- Mobile nav uses CSS transitions, not JS animation library
- `date-fns` `formatDistanceToNow` is already a dependency — no bundle size increase for stale time
- Global reduced-motion rule is pure CSS — zero JS cost

---

## Success Metrics

| Metric                   | Target                                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| Visual hierarchy clarity | Hero has 5-6 elements with clear priority, not 8 elements competing                                    |
| Double footer            | Gone                                                                                                   |
| Badge accuracy           | No "Real-Time" or "LIVE" claims that contradict actual data freshness                                  |
| Accessibility            | `prefers-reduced-motion` supported; keyboard nav has visible focus rings; no `dangerouslySetInnerHTML` |
| Mobile usability         | Nav accessible on mobile; mobile hint uses safe rendering                                              |
| Build health             | `npm run build` passes, tests pass, no TS errors                                                       |
| Premium feel             | Generous spacing, clear hierarchy, restrained motion, honest copy                                      |

---

## Rollback

All changes are in existing files on the `ui/premium-ux-upgrade` branch. Rollback = `git checkout main -- <files>`. No database changes. No dependency changes. No build config changes.
