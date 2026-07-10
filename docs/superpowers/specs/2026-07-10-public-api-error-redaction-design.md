# Public API Error Redaction Design

## Context

The maintenance audit identifies a focused security-hardening task: public API
500 responses must log server failures internally without returning raw
exception details to clients. Seventeen Next.js route handlers currently place
`error.message` in a 500 response. Those messages can contain database,
infrastructure, or implementation details.

The change must remain compatible with existing API consumers. Status codes,
headers, response fields, static route-specific error summaries, and successful
responses are outside the scope of this batch.

## Decision

Add a small shared utility, `getPublicApiErrorMessage(error: unknown)`, that
intentionally discards the supplied value and returns `"Internal server error"`.
Every exception-derived value in a public 500 response will use this utility.

Each route will continue to log the original exception through its existing
logger or `console.error` call before constructing the response. The utility
will not log because it lacks route context and duplicate logging would reduce
signal quality.

Existing JSON shapes remain unchanged:

- responses with an `error` field only keep that field;
- responses with both a route-specific `error` summary and a `message` field
  keep both fields, with only `message` redacted;
- the health response keeps its diagnostic metadata and redacts only its
  exception-derived `error` value;
- all existing status codes, no-store headers, and static safe messages remain
  unchanged.

## Scope

Redact exception-derived 500 response values in these route groups:

- analytics: benchmarks, patterns, regions, and trends;
- hospital data: anomalies, compare, data quality, hospitals, and methodology;
- export and health;
- resources: alerts, AQHI, resource index, system context, and water advisories;
- system status.

Three raw-message uses are deliberately retained because they are not exposed
in a 500 response:

- equity summary uses the message to classify a missing layer;
- equity layer uses the message to select a 404 response;
- resource alerts includes the message only in an internal enrichment warning.

Routes whose 500 responses already contain only static safe text do not need a
behavior change.

## Error Flow

1. A route dependency throws.
2. The route logs the original exception with its existing route context.
3. Any existing client-error classification runs unchanged (for example, the
   temporal-pattern invalid-lookback 400 path).
4. A true 500 response preserves its existing envelope but replaces the raw
   exception-derived value with `getPublicApiErrorMessage(error)`.
5. The client receives no exception text.

## Validation

Use test-driven development:

- add utility tests that pass secret-like `Error`, string, object, and undefined
  values and assert the output is always the generic message;
- update or add one failure-path route test for each affected route, asserting
  the existing status and response shape, the generic value, and absence of the
  injected private marker;
- retain tests proving classified client errors still return their existing
  4xx response;
- run targeted redaction tests first, then the complete frontend unit suite,
  lint, formatting check, TypeScript application/test checks, and build under
  the repository-pinned Node 22.13.1 runtime;
- use a final source scan to confirm no exception-derived value remains in a
  public 500 response.

## Alternatives Considered

1. **Shared redaction utility (selected).** Centralizes the security invariant,
   preserves every response contract, and makes the intent testable.
2. **Inline generic literals.** Smaller initial diff, but repeats a security
   decision across many handlers and makes drift more likely.
3. **Normalize all 500 responses to a new common envelope.** Architecturally
   tidy, but changes public contracts and is unnecessary for this maintenance
   objective.

## Completion Criteria

- No public API 500 response serializes raw exception details.
- Original exceptions remain available in internal logs.
- Existing response shapes, status codes, headers, and safe static summaries
  are preserved.
- Every changed failure path has an automated regression assertion.
- The maintenance audit and planning index record the delivered work so it is
  not selected again.
