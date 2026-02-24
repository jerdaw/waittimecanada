# Home Page Premium UX Analysis

**Analyzed:** 2026-02-24
**Branch:** `ui/premium-ux-upgrade`
**Scope:** `frontend/app/[locale]/page.tsx`, Hero, Header, Footer, AboutSection, AccessInsightsSummary, RegionDashboard, HeroStats, HeroHowItWorks, ProvinceCoverage, Testimonial, translation keys (EN/FR)

---

## Phase 0 — Grounding Summary

| Aspect | Finding |
|--------|---------|
| **Framework** | Next.js 14 App Router, `[locale]` dynamic segment, most pages `"use client"` |
| **Page architecture** | Homepage is a single `"use client"` component (~460 lines) managing ~15 pieces of state. Layout wraps all pages with `EmergencyBanner`, `StructuredData`, `Footer`. |
| **Styling** | Tailwind CSS with CSS-variable design tokens for colors, shadows, radii. No component library (no shadcn/ui). All components use ad-hoc Tailwind classes. |
| **Design tokens** | Well-structured: `--primary`, `--muted`, `--border`, `--card`, `--success`, `--warning`, `--danger`. Light/dark parity via `.dark` class override. |
| **Typography** | Inter via Google Fonts, `font-feature-settings: cv02, cv03, cv04, cv11`. No formal type scale tokens — sizes are ad-hoc (`text-xs`, `text-sm`, `text-lg`, etc.). |
| **Motion** | Custom Tailwind keyframes (`fade-in`, `slide-up`, `scale-in`, `pulse-soft`). Also uses `animate-in` pattern with inline delay classes. No animation library. `prefers-reduced-motion` is **not** respected anywhere. |
| **i18n** | `next-intl` v4.8.3. All visible text uses `useTranslations('Namespace')`. EN + FR message files. |
| **Icons** | `lucide-react` for most icons. Hero uses inline SVGs instead of Lucide (inconsistency). |
| **Reusable components** | None at the primitive level. No shared Button, Card, Input, Badge. Each component reinvents these patterns. |
| **Double Footer** | `layout.tsx` renders `<Footer />` globally. Homepage *also* renders `<Footer />` conditionally when `!showHero`. This means the footer appears twice after hero dismissal. Other pages (analytics, data-quality, etc.) render their own `<Footer />` too — tripling it in some cases. |
| **Performance** | Homepage is entirely client-rendered. Geolocation fires on mount. Two `useEffect` fetches (hospitals + regions). No `React.memo`, no virtualization on the main list (HospitalList uses `react-window` internally). |
| **Conversion goal** | Get visitors to dismiss the hero and explore hospital wait times; secondarily, convey methodological rigor for admissions committee review. |

---

## Executive Summary

The homepage has a solid foundation after the first improvement pass (HeroStats, ProvinceCoverage, HeroHowItWorks, province pills, benefit-focused copy). However, it still has significant **structural, polish, and UX issues** that prevent it from feeling truly premium:

1. **Double footer bug** — layout.tsx renders Footer globally, and the homepage renders it again conditionally. This is the most visible regression.
2. **Hero is visually cluttered** — badge + stats bar + H1 + description + province pills + CTAs + ProvinceCoverage strip + HeroHowItWorks all stack vertically with similar visual weight. There's no breathing room or clear hierarchy.
3. **Featured card shows stale "LIVE" badge** — the card always shows "LIVE" even when `last_updated` may be hours old. The `updatedNow` issue from the old plan is still present.
4. **No reduced-motion support** — all animations ignore `prefers-reduced-motion`. This is an accessibility gap.
5. **Inconsistent interactive patterns** — buttons/links use different styling approaches. No shared primitive exists.
6. **Empty testimonial** — `stakeholderTestimonials` array is still empty, so the Testimonial section renders nothing. The conditional rendering is correct but the feature delivers zero value.
7. **Mobile experience gaps** — split view hides the list on mobile. The mobile hint uses `dangerouslySetInnerHTML` for a simple `<strong>` tag.
8. **Information density after hero dismiss** — AccessInsightsSummary + RegionDashboard + split view + AboutSection + Footer all appear at once, with no progressive disclosure.

---

## Top 10 Highest-Impact Improvements

| # | Improvement | Impact | Effort | Type |
|---|-------------|--------|--------|------|
| 1 | **Fix double footer** — remove `<Footer />` from homepage (layout already provides it) | High | Low | Bug/UX |
| 2 | **Simplify hero vertical stack** — reduce visual clutter by consolidating or removing redundant elements (HeroStats + ProvinceCoverage overlap in messaging) | High | Medium | UI/Hierarchy |
| 3 | **Add `prefers-reduced-motion` support** — wrap all `animate-in` usage and keyframe animations | High | Low | A11y |
| 4 | **Fix featured card LIVE accuracy** — derive "LIVE" / "Updated X ago" from actual `last_updated` timestamp | High | Low | Trust/Accuracy |
| 5 | **Improve hero spacing and rhythm** — increase whitespace between sections, use consistent spacing tokens | High | Low | UI/Polish |
| 6 | **Consolidate hero trust signals** — merge HeroStats + ProvinceCoverage into a single, tighter trust strip | Medium | Medium | UI/Conversion |
| 7 | **Replace `dangerouslySetInnerHTML` in mobile hint** — use `t.rich()` instead for safety and consistency | Medium | Low | Performance/Security |
| 8 | **Add subtle hover/focus states to province pills** — current hover is minimal, focus ring is missing for keyboard nav | Medium | Low | A11y/Interaction |
| 9 | **Improve AboutSection visual weight** — currently has equal visual weight to content sections; should feel more like a subtle aside | Medium | Low | UI/Hierarchy |
| 10 | **Tighten header/nav consistency** — nav links on desktop lack active state; mobile has no nav at all (hamburger menu missing) | Medium | Medium | UX/Mobile |

---

## Detailed Observations

### A. Messaging & Copy Clarity

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| A1 | Hero title "Canada ER Wait Time Observatory" is split across 3 lines (`title` + `subtitle` + `subtitle2`) creating awkward reading rhythm. The `<br />` between subtitle and subtitle2 is rigid. | Medium | Low | Copy/UI |
| A2 | Description copy is strong ("See real wait times... with full transparency... No hidden assumptions.") — keep as-is. | — | — | ✅ |
| A3 | "Explore Hospitals" CTA is clear and action-oriented — good. | — | — | ✅ |
| A4 | "How We Measure This" secondary CTA is improved from old "Understand Methodologies" — good. | — | — | ✅ |
| A5 | HeroStats pills ("4 Provinces", "{count}+ Hospitals", "Fresh Data Every 4 Hours") overlap conceptually with ProvinceCoverage strip below. User sees province info twice. | Medium | Medium | Copy/UX |
| A6 | "Fresh Data Every 4 Hours" — the word "Fresh" is informal for a clinical observatory. Consider "Updated Every 4 Hours". | Low | Low | Copy/Tone |
| A7 | Badge "Real-Time Canadian ER Data" says "Real-Time" but data is updated every 4 hours — a contradiction that could undermine trust. | High | Low | Copy/Trust |
| A8 | `HomePage.mobileHint` uses `t.raw('mobileHint')` with `dangerouslySetInnerHTML` — should use `t.rich()` with a `strong` renderer. | Medium | Low | Security |

### B. Value Proposition & Conversion

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| B1 | Hero dismissal is one-way — no way to return to hero without page refresh. | Medium | Low | UX |
| B2 | Province quick-pick pills in hero are functional and correctly synced with page state — good. | — | — | ✅ |
| B3 | Featured hospital card is the strongest conversion element. The glow effect, wait time typography, and methodology badge work well. | — | — | ✅ |
| B4 | Featured card "LIVE" badge is always shown regardless of data freshness. If `last_updated` is >4h old, "LIVE" is misleading. | High | Low | Trust |
| B5 | Featured card click dismisses hero AND selects hospital — correct and intuitive. | — | — | ✅ |
| B6 | After hero dismiss, the user immediately sees AccessInsightsSummary + RegionDashboard which is dense. Consider a smoother transition. | Medium | Medium | UX |
| B7 | No scroll indicator or visual cue that content exists below the hero section on initial load. | Low | Low | UX |

### C. Visual Hierarchy & Layout

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| C1 | **Double footer bug**: `layout.tsx:78` renders `<Footer />`. `page.tsx:455-457` also renders `<Footer />` when `!showHero`. Two footers visible after hero dismiss. | High | Low | Bug |
| C2 | Hero vertical stack has 8 distinct visual elements with similar weight: badge, stats bar, H1, description, province pills, CTAs, ProvinceCoverage, HeroHowItWorks. Needs consolidation. | High | Medium | UI |
| C3 | `HeroHowItWorks` is desktop-only (`hidden lg:block`) and sits below the fold even on large screens. Low visibility. | Medium | Low | UI |
| C4 | ProvinceCoverage strip is visually similar to province pills above it — redundant. Pills show province codes (ON, QC, AB, BC); strip shows province codes + official source names. | Medium | Medium | UI |
| C5 | Map/list split view uses hardcoded `35%/65%` ratio on desktop. The list panel feels narrow for 380+ hospitals. | Low | Low | UI |
| C6 | No section dividers or subtle transitions between hero → insights → split view → about → footer. Content flows without rhythm. | Medium | Low | UI |
| C7 | `max-w-6xl` in hero vs `max-w-screen-2xl` in split view creates a visual width jump. | Low | Low | UI |
| C8 | Hero section has `min-h-[40vh]` which on tall screens creates too much dead space; on short screens, the stacked content overflows. | Low | Medium | UI/Mobile |

### D. Trust & Credibility

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| D1 | Badge "Real-Time" contradicts "Every 4 Hours" stat pill — pick one message. | High | Low | Trust |
| D2 | ProvinceCoverage strip showing official source names (Ontario Health, Québec MSSS, etc.) is a strong trust signal — keep. | — | — | ✅ |
| D3 | AboutSection author bio is a strength for the admissions narrative — but currently buried at bottom of page, only visible after hero dismiss. | Medium | Low | Trust |
| D4 | No methodology badge or "how this was measured" context on the featured hospital card footer shows methodology family — good. | — | — | ✅ |
| D5 | EmergencyBanner (sticky red 911 banner) is in layout — good safety signal. | — | — | ✅ |
| D6 | GitHub link is only in footer and AboutSection — could be a subtle trust signal in header. | Low | Low | Trust |

### E. Interaction & Motion

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| E1 | **No `prefers-reduced-motion` respect** — all `animate-in`, ping animations, hover transforms play unconditionally. Accessibility gap. | High | Low | A11y |
| E2 | Hero stagger animations (delay-100/200/300) are well-executed and appropriately subtle. | — | — | ✅ |
| E3 | Featured card hover state is subtle (border color change, name color change) — good restraint. | — | — | ✅ |
| E4 | Province pills have no focus ring for keyboard navigation. `aria-pressed` is correctly set. | Medium | Low | A11y |
| E5 | Hero dismiss is instant (CSS `animate-in fade-in` on new content) — no exit animation on hero. Feels abrupt. | Low | Medium | Motion |
| E6 | `animate-ping` on badge dot and LIVE dot runs infinitely — can be distracting. Consider `pulse-soft` instead. | Low | Low | Motion |
| E7 | Featured card glow uses `blur-2xl` which is heavy on GPU — acceptable on modern browsers but no fallback. | Low | Low | Performance |

### F. Mobile Experience

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| F1 | Split view hides list on mobile (`hidden lg:block`). Map fills screen. Only hint is a small text line using `dangerouslySetInnerHTML`. | High | Low | Mobile |
| F2 | Header has no mobile navigation (hamburger/drawer). Desktop nav (`hidden md:flex`) is completely inaccessible on mobile. | High | Medium | Mobile |
| F3 | Hero stacks vertically on mobile with all 8 elements — very long scroll to reach CTAs. | Medium | Medium | Mobile |
| F4 | `HeroHowItWorks` is correctly hidden on mobile — good decision. | — | — | ✅ |
| F5 | Province pills wrap nicely on small screens — good. | — | — | ✅ |
| F6 | Featured card (`max-w-sm`) is appropriately sized for mobile. | — | — | ✅ |
| F7 | Mobile search in stats bar has `max-w-[200px]` which may truncate on very small screens. | Low | Low | Mobile |
| F8 | Touch targets on province pills (px-4 py-1.5) meet minimum 44px height when accounting for font size. Borderline. | Low | Low | Mobile/A11y |

### G. Accessibility

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| G1 | `prefers-reduced-motion` not supported — critical gap. | High | Low | A11y |
| G2 | Province pills have `aria-pressed` — good. Missing focus-visible ring. | Medium | Low | A11y |
| G3 | `aria-label` on explore button duplicates visible text — redundant but not harmful. | Low | Low | A11y |
| G4 | Inline SVGs in Hero and Header lack consistent `aria-hidden="true"` — some have it, some don't. | Low | Low | A11y |
| G5 | `AboutSection` has proper `aria-expanded` — good. | — | — | ✅ |
| G6 | Header search input has placeholder text but no visible label — screen reader relies on placeholder which is not ideal. | Medium | Low | A11y |
| G7 | Mobile hint uses `dangerouslySetInnerHTML` which bypasses React's XSS protection. Content is from translation file (safe) but pattern is bad practice. | Medium | Low | A11y/Security |
| G8 | Color contrast: `text-muted-foreground` (#71717a on #ffffff) has ratio ~4.63:1 — passes AA for normal text but fails AAA. Acceptable. | Low | Low | A11y |

### H. Performance & Maintainability

| # | Observation | Impact | Effort | Type |
|---|------------|--------|--------|------|
| H1 | Homepage is entirely client-rendered (`"use client"`). Could benefit from server components for static portions (Header, Footer, AboutSection). However, the page's interactivity requirements make this a low-priority refactor. | Low | High | Performance |
| H2 | Two `useEffect` fetches on mount (hospitals + regions) could be combined or use React Query. Low priority — works correctly. | Low | High | Performance |
| H3 | `filteredAndSortedHospitals` recomputes on every render. Already uses `[...hospitals]` spread. Could be wrapped in `useMemo`. | Low | Low | Performance |
| H4 | Hero inline SVGs should be replaced with Lucide icons for consistency and bundle size. | Low | Low | Maintainability |
| H5 | No shared Button component — hero CTA, province pills, featured card button all have different styling. | Medium | Medium | Maintainability |
| H6 | Global `* { transition-property: background-color, border-color }` in globals.css applies to ALL elements including SVGs and layout containers. Could cause subtle rendering issues. | Low | Low | Performance |

---

## What to Simplify/Remove

| Item | Rationale |
|------|-----------|
| **Remove `<Footer />` from `page.tsx`** | Layout already renders it globally. Duplicate. |
| **Remove or consolidate HeroStats** | Province count overlaps with province pills and ProvinceCoverage. Hospital count is in the description. Cadence is the only unique stat. Consider folding the cadence note into the badge or description. |
| **Remove `dangerouslySetInnerHTML` in mobile hint** | Replace with `t.rich()` pattern already used elsewhere. |
| **Remove redundant `aria-label` on explore button** | Button text is already descriptive. `aria-label` that duplicates visible text is unnecessary. |
| **Simplify hero vertical stack** | 8 visual elements with similar weight → aim for 5-6 with clear hierarchy. |
| **Remove or make conditional the "LIVE" badge** | Only show when data is actually recent (< 1 hour). |
| **Consider removing HeroHowItWorks from hero** | It's desktop-only, below the fold, and adds visual weight. The 3 steps could be moved to the FAQ or a separate section. |

---

## Premium Aesthetic Risks

| Risk | Current State | Mitigation |
|------|--------------|------------|
| **Glow effect on featured card** | `blur-2xl` gradient glow with `opacity-40` → `opacity-60` on hover. Currently restrained and appropriate. | Keep as-is. Do not increase opacity or add more glow effects. |
| **Dot grid pattern in hero** | `opacity-[0.15]` — subtle and appropriate. | Do not increase opacity. |
| **Gradient overlays in hero** | Two `blur-3xl` circles with `bg-primary/5` and `bg-accent/5`. Very subtle. | Keep restrained. Do not add more gradient elements. |
| **`animate-ping` on badge/LIVE dots** | Continuous animation draws attention. Two ping animations on screen at once (badge + card) compete. | Replace badge ping with `pulse-soft` (less aggressive). Keep card ping. |
| **Gradient top bar on featured card** | `from-primary via-accent to-primary` — tasteful but close to the line. | Keep as-is. Do not add gradient bars to other elements. |
| **Province pills active state** | `shadow-sm shadow-primary/20` — subtle. | Do not add glow to pills. |
| **Overall hero density** | The hero tries to do too much. Each element is individually tasteful but together they create visual noise. | The biggest aesthetic risk is **clutter, not flash**. Reduce elements or increase spacing. |

---

## Summary

The homepage has a strong functional foundation. The main issues are structural (double footer, hero density, missing mobile nav) rather than aesthetic. The design token system is solid. The biggest opportunity is **editing down** — removing redundancy and increasing breathing room — rather than adding new elements. The premium feeling should come from **restraint and clarity**.
