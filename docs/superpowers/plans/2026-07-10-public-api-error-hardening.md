# Public API Error Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent all exception-derived server details from appearing in public API 500 responses while preserving every existing response contract.

**Architecture:** A focused `getPublicApiErrorMessage(error: unknown): string` utility owns the redaction invariant and always returns `"Internal server error"`. Existing route catch blocks continue logging the original exception, then use the utility only for exception-derived response fields; route-specific static summaries, client-error classification, status codes, headers, and JSON shapes remain unchanged.

**Tech Stack:** Next.js 15 route handlers, TypeScript 5, Vitest 4, Node.js 22.13.1, ESLint, Prettier.

**Status:** Complete on 2026-07-10. All 17 affected route handlers use the
shared redaction invariant, all planned regression coverage is present, and the
validation commands below passed.

## Global Constraints

- Never inspect or print `.env*`, credentials, keys, certificates, or private maintainer notes.
- Preserve every existing JSON field, safe static message, HTTP status, and response header.
- Keep original exceptions in existing internal logs; do not add duplicate logging to the utility.
- Retain error-message classification used for intentional 4xx responses.
- Use the repository-pinned Node.js 22.13.1 runtime for authoritative frontend validation.
- Write each behavior assertion before changing its route implementation.
- Do not deploy, publish, modify secrets, or perform remote environment actions.

---

### Task 1: Central Redaction Invariant

**Files:**
- Create: `frontend/utils/apiErrors.test.ts`
- Create: `frontend/utils/apiErrors.ts`

**Interfaces:**
- Consumes: any caught value as `unknown`
- Produces: `getPublicApiErrorMessage(error: unknown): string`

- [x] **Step 1: Write the failing utility test**

```ts
import { describe, expect, it } from "vitest";
import { getPublicApiErrorMessage } from "./apiErrors";

describe("getPublicApiErrorMessage", () => {
  it.each([
    new Error("PRIVATE_MARKER database.internal:5432"),
    "PRIVATE_MARKER string failure",
    { detail: "PRIVATE_MARKER object failure" },
    undefined,
  ])("redacts exception details from %o", (error) => {
    const message = getPublicApiErrorMessage(error);

    expect(message).toBe("Internal server error");
    expect(message).not.toContain("PRIVATE_MARKER");
  });
});
```

- [x] **Step 2: Run the test and verify the missing module failure**

Run:

```bash
cd frontend
npx vitest run utils/apiErrors.test.ts
```

Expected: FAIL because `./apiErrors` does not exist.

- [x] **Step 3: Add the minimal utility**

```ts
export function getPublicApiErrorMessage(error: unknown): string {
  void error;
  return "Internal server error";
}
```

- [x] **Step 4: Run the utility test**

Run: `cd frontend && npx vitest run utils/apiErrors.test.ts`

Expected: 1 test file passes with 4 table cases.

- [x] **Step 5: Commit the invariant**

```bash
git add frontend/utils/apiErrors.ts frontend/utils/apiErrors.test.ts
git commit -m "test: define public API error redaction invariant"
```

### Task 2: Analytics Route Redaction

**Files:**
- Modify: `frontend/tests/api/analytics-benchmarks.test.ts`
- Modify: `frontend/tests/api/analytics-patterns.test.ts`
- Modify: `frontend/tests/api/analytics-regions.test.ts`
- Modify: `frontend/tests/api/analytics-trends.test.ts`
- Modify: `frontend/app/api/analytics/benchmarks/route.ts`
- Modify: `frontend/app/api/analytics/patterns/route.ts`
- Modify: `frontend/app/api/analytics/regions/route.ts`
- Modify: `frontend/app/api/analytics/trends/route.ts`

**Interfaces:**
- Consumes: `getPublicApiErrorMessage(error)` from Task 1
- Produces: unchanged analytics envelopes whose `message` is generic on 500

- [x] **Step 1: Tighten all four database-failure tests**

In each existing failure test, inject `new Error("PRIVATE_MARKER ...")` and add:

```ts
expect(response.status).toBe(500);
expect(json.message).toBe("Internal server error");
expect(JSON.stringify(json)).not.toContain("PRIVATE_MARKER");
```

Retain each existing route-specific `json.error` assertion. In the patterns
suite, retain the existing invalid-lookback test to protect the classified 400
response.

- [x] **Step 2: Run the four test files and verify they fail on leaked messages**

```bash
cd frontend
npx vitest run \
  tests/api/analytics-benchmarks.test.ts \
  tests/api/analytics-patterns.test.ts \
  tests/api/analytics-regions.test.ts \
  tests/api/analytics-trends.test.ts
```

Expected: the new generic-message assertions fail.

- [x] **Step 3: Redact only the true 500 values**

Add this import to each route:

```ts
import { getPublicApiErrorMessage } from "@/utils/apiErrors";
```

Use this field in benchmarks, regions, and trends:

```ts
message: getPublicApiErrorMessage(error),
```

Patterns must keep its local raw `message` for invalid-lookback classification,
but its final 500 envelope must use:

```ts
message: getPublicApiErrorMessage(error),
```

- [x] **Step 4: Re-run analytics tests**

Run the Step 2 command.

Expected: all four files pass, including the existing 400 classification test.

- [x] **Step 5: Commit analytics routes**

```bash
git add frontend/app/api/analytics frontend/tests/api/analytics-*.test.ts
git commit -m "fix: redact analytics API server errors"
```

### Task 3: Core Data Route Redaction

**Files:**
- Modify tests: `frontend/app/api/anomalies/route.test.ts`, `frontend/app/api/compare/route.test.ts`, `frontend/app/api/data-quality/route.test.ts`, `frontend/app/api/export/route.test.ts`, `frontend/app/api/health/route.test.ts`, `frontend/app/api/hospitals/route.test.ts`, `frontend/app/api/methodology/route.test.ts`, `frontend/app/api/status/route.test.ts`
- Modify matching handlers: `frontend/app/api/anomalies/route.ts`, `frontend/app/api/compare/route.ts`, `frontend/app/api/data-quality/route.ts`, `frontend/app/api/export/route.ts`, `frontend/app/api/health/route.ts`, `frontend/app/api/hospitals/route.ts`, `frontend/app/api/methodology/route.ts`, `frontend/app/api/status/route.ts`

**Interfaces:**
- Consumes: `getPublicApiErrorMessage(error)` from Task 1
- Produces: unchanged core route envelopes with generic exception-derived fields

- [x] **Step 1: Add a private marker to each failure path**

Extend the existing rejected-database tests, or add an equivalent test using
the file's existing mocked `getDb`, with these exact assertions:

```ts
expect(response.status).toBe(500);
expect(JSON.stringify(data)).not.toContain("PRIVATE_MARKER");
```

For anomalies, data quality, methodology, and status:

```ts
expect(data.error).toBe("Internal server error");
```

For compare, export, and hospitals:

```ts
expect(data.message).toBe("Internal server error");
```

For health, retain all existing degraded-health metadata assertions and add:

```ts
expect(data.error).toBe("Internal server error");
```

- [x] **Step 2: Run the eight route suites and verify failure**

```bash
cd frontend
npx vitest run \
  app/api/anomalies/route.test.ts \
  app/api/compare/route.test.ts \
  app/api/data-quality/route.test.ts \
  app/api/export/route.test.ts \
  app/api/health/route.test.ts \
  app/api/hospitals/route.test.ts \
  app/api/methodology/route.test.ts \
  app/api/status/route.test.ts
```

Expected: newly added generic-message assertions fail.

- [x] **Step 3: Replace each exception-derived response field**

Import the Task 1 utility in all eight routes. Replace each direct conditional
serialization with:

```ts
getPublicApiErrorMessage(error)
```

Keep the surrounding `error:` or `message:` property name and all other body
fields unchanged.

- [x] **Step 4: Re-run core route tests**

Run the Step 2 command.

Expected: all eight files pass.

- [x] **Step 5: Commit core routes**

```bash
git add frontend/app/api/anomalies frontend/app/api/compare \
  frontend/app/api/data-quality frontend/app/api/export \
  frontend/app/api/health frontend/app/api/hospitals \
  frontend/app/api/methodology frontend/app/api/status
git commit -m "fix: redact core API server errors"
```

### Task 4: Resource Route Redaction

**Files:**
- Modify tests: `frontend/app/api/resources/alerts/route.test.ts`, `frontend/app/api/resources/aqhi/route.test.ts`, `frontend/app/api/resources/route.test.ts`, `frontend/app/api/resources/system-context/route.test.ts`, `frontend/app/api/resources/water-advisories/route.test.ts`
- Modify matching handlers under `frontend/app/api/resources/`

**Interfaces:**
- Consumes: `getPublicApiErrorMessage(error)` from Task 1
- Produces: unchanged resource error envelopes with a generic `message` on 500

- [x] **Step 1: Add one database-failure assertion per route**

Use each suite's existing database mock to reject with
`new Error("PRIVATE_MARKER resource database detail")`, call the route with a
valid request, and assert:

```ts
expect(response.status).toBe(500);
expect(data.success).toBe(false);
expect(data.message).toBe("Internal server error");
expect(JSON.stringify(data)).not.toContain("PRIVATE_MARKER");
```

Retain each route-specific static `data.error` summary.

- [x] **Step 2: Run resource tests and verify failure**

```bash
cd frontend
npx vitest run \
  app/api/resources/alerts/route.test.ts \
  app/api/resources/aqhi/route.test.ts \
  app/api/resources/route.test.ts \
  app/api/resources/system-context/route.test.ts \
  app/api/resources/water-advisories/route.test.ts
```

Expected: the new generic-message assertions fail.

- [x] **Step 3: Redact resource 500 response messages**

Import `getPublicApiErrorMessage` and set each top-level catch envelope to:

```ts
message: getPublicApiErrorMessage(error),
```

Do not change the alerts DPD-enrichment warning; it is internal logging and not
a public response.

- [x] **Step 4: Re-run resource tests**

Run the Step 2 command.

Expected: all five files pass, including the DPD graceful-degradation test.

- [x] **Step 5: Commit resource routes**

```bash
git add frontend/app/api/resources
git commit -m "fix: redact resource API server errors"
```

### Task 5: Close Documentation And Validate The Batch

**Files:**
- Modify: `docs/maintenance-audit.md`
- Modify: `docs/planning/README.md`
- Update in place: `docs/superpowers/plans/2026-07-10-public-api-error-hardening.md`

**Interfaces:**
- Consumes: passing route behavior from Tasks 1-4
- Produces: durable completion evidence and no remaining actionable audit item

- [x] **Step 1: Run a source-level leak audit**

```bash
git grep -n -E 'error instanceof Error \? error\.message|error\.message' -- frontend/app/api
git grep -n -C 5 -E 'status:[[:space:]]*500' -- frontend/app/api
```

Expected: remaining raw-message occurrences are limited to equity-summary 404
classification, equity-layer 404 classification, patterns 400 classification,
and alerts internal logging; no 500 response contains one.

- [x] **Step 2: Run targeted and full frontend validation**

```bash
cd frontend
npm run test:unit
npm run lint
npm run format:check
npm run type-check
npm run type-check:test
npm run build
```

Expected: every command exits 0 under Node 22.13.1.

- [x] **Step 3: Run repository documentation checks**

```bash
bash scripts/check-docs.sh
git diff --check
```

Expected: both commands exit 0.

- [x] **Step 4: Record completion**

Update the maintenance-audit deferred findings and final recommendations to
state that the 2026-07-10 focused pass delivered centralized redaction and
route-by-route regression coverage. Mark every checkbox in this plan complete,
record the exact verification totals, and list this plan as a closed delivered
artifact in `docs/planning/README.md`.

- [x] **Step 5: Commit completion evidence**

```bash
git add docs/maintenance-audit.md docs/planning/README.md \
  docs/superpowers/plans/2026-07-10-public-api-error-hardening.md
git commit -m "docs: record API error hardening completion"
```

- [x] **Step 6: Verify the clean committed tree**

Re-run the commands from Steps 1-3, then run:

```bash
git status --short --branch
git log -6 --oneline
```

Expected: the branch is clean and the committed validation remains green.
