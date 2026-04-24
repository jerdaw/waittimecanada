# Repo Audit Remediation Plan (2026-04-23)

**Status:** Active planning only
**Related:** `2026-04-23-repo-audit-follow-up-board.md`, `roadmap.md`, `docs/operations/direct-vps-frontend.md`, `docs/operations/direct-vps-backend.md`

## Summary

This plan turns the 2026-04-23 audit board into one ordered remediation track
for Wait Time Canada.

No fixes are applied here. This is sequencing only.

## Priority Sequence

### Track 1: Current Runtime And Privacy Truth

Why first:

1. the current frontend-on-VPS and backend-on-GitHub-Actions split needs one
   clean operator and user-facing narrative
2. public privacy language currently understates real visitor-data handling

Scope:

1. reconcile `README.md`, `docs/README.md`, roadmap, and deployment blockers
   against the April 2026 runtime baseline
2. create one visitor-data inventory covering IP handling, geolocation,
   third-party requests, and request metadata
3. align privacy copy to actual runtime behavior

Exit criteria:

1. start-here docs clearly reflect the current split-runtime baseline
2. privacy copy can be mapped to actual geolocation, logging, and third-party
   behavior

### Track 2: Test And CI Reality

Why second:

1. backend integration and E2E claims currently overstate merge-readiness
2. this drift can mislead future planning and regression confidence

Scope:

1. decide whether backend integration coverage becomes a real CI lane or the
   docs step back from current claims
2. decide which frontend browser flows need automatic coverage
3. re-baseline README and planning claims on current automated evidence

Exit criteria:

1. test-count and coverage claims match the enforced reality
2. the repo has an explicit stance on backend integration and frontend browser
   gating

### Track 3: Browser Security Posture

Why third:

1. CSP and header enforcement are important, but they are easier to tighten
   once runtime and test truth are clean
2. the current posture is incomplete rather than obviously broken

Scope:

1. decide whether report-only CSP is temporary or accepted steady state
2. add header-verification expectations to future CI or smoke planning
3. align old hosting-era security language with the current VPS contract

Exit criteria:

1. CSP posture has an explicit target state
2. security-header verification is part of a defined future enforcement path

### Track 4: Structural Backend Boundaries

Why last:

1. the growing data-access layer matters, but it is less urgent than the
   documentation, privacy, and CI drift above

Scope:

1. plan a boundary split for backend data-access and aggregation concerns
2. define which domain seams should stop accumulating inside the current
   database service layer

Exit criteria:

1. a bounded future decomposition target exists before implementation starts

## Non-Goals

1. no runtime migration decision change by itself
2. no scraper or frontend implementation fixes in this document
3. no hosting-platform expansion
