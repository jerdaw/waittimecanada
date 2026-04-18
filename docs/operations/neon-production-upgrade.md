# Production Neon Upgrade Runbook

**Status:** Completed in production on 2026-04-16; retained as current reference
**Last Updated:** 2026-04-18
**Applies To:** Production Neon project for `waittimecanada`

## Purpose

This runbook records the production database cost/reliability follow-up after
the March 28, 2026 transfer-quota outage.

The production project was confirmed on Neon Launch on **2026-04-18**, with the
current billing period showing a start date of **2026-04-16**.

Keep this document as the reference for what was done and for future billing
posture re-verification.

## Why This Is Needed

Production already experienced:

- a real Neon transfer-quota outage on **2026-03-28**
- an **89% storage warning** on **2026-03-31**

Frontend cache guardrails and bounded cleanup reduced pressure, but the current
roadmap position is that the **free tier is no longer acceptable for
production**. The recommended production posture is Neon **Launch** plus
follow-up monitoring for at least one billed month.

See:

- `docs/planning/roadmap.md`
- `docs/planning/manual-tasks.md`
- `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`

## Preconditions

- Production is currently healthy:
  - `https://wait-time.ca/api/health`
  - `https://wait-time.ca/api/status`
  - `https://wait-time.ca/api/data-quality`
- You have access to the Neon project billing page for the production project.
- You are ready to record the change in the roadmap/manual-task docs after the
  billing update is complete.

## Manual Upgrade Checklist

1. Open the production Neon project used by `waittimecanada`.
2. Confirm you are on the correct project before changing billing.
3. Open the billing/plan page.
4. Upgrade the project from the free tier to the **Launch** plan.
5. Record the exact upgrade date in your notes.
6. Confirm the plan change is reflected in the Neon dashboard.
7. Review current storage and transfer usage after the plan change.

## Completion Record

- Neon dashboard confirmed **Launch** active
- Current billing period observed as **2026-04-16 to 2026-05-01**
- Live verification re-passed on **2026-04-18**

## Expected Runtime Impact

- No application code change is required.
- No environment variable change is expected.
- No frontend redeploy is required solely for the plan upgrade.
- Public endpoints should remain stable before and after the billing change.

## Verification After Upgrade

Run these checks after the plan change:

```bash
curl -fsS https://wait-time.ca/api/health
PRODUCTION_BASE_URL=https://wait-time.ca ./scripts/production-smoke.sh
```

Recommended additional checks:

```bash
curl -fsS https://wait-time.ca/api/status
curl -fsS https://wait-time.ca/api/data-quality
```

## Repo Follow-Up

After the plan change is confirmed:

1. Update `docs/planning/roadmap.md`
   - mark the Neon upgrade roadmap item complete
   - record the date of the billing change
2. Update `docs/planning/manual-tasks.md`
   - move the Neon Launch task from ready to completed
3. If useful, add a short maintenance archive note for the session that closes
   the item

## Monitoring Window

After the upgrade:

- watch Neon transfer/storage trends for at least one billed month
- keep existing frontend read-cache and cleanup guardrails in place
- only revisit self-hosting or deeper DB-path changes if cost/reliability
  pressure remains meaningful even on Launch

## Optional Credit Follow-Up

After Launch is active, optionally apply to the Neon Open Source Program:

- this is a cost-offset follow-up, not a blocker
- if approved, record the outcome in `docs/planning/roadmap.md`

## Do Not Do

- Do not change scraper cadence purely because the plan was upgraded.
- Do not treat the billing change as permission to remove retention guardrails.
- Do not reopen backend VPS cutover work as part of this task.
