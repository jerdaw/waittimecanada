# Stewardship Triggers

This file is not an open task list. Wait Time Canada has no scheduled human
maintenance cadence, external-operations campaign, methodology project, or
expansion queue. Private deployment runbooks, credentials, monitoring
configuration, and private operational notes remain outside public
documentation.

## Current State

- Routine source collection and heartbeat checks are automated.
- One newly opened or changed source-health incident may request one bounded
  freshness-only recovery. An unchanged incident remains visible and failed but
  does not repeatedly dispatch repair work.
- Human action is event-triggered. A red workflow caused by a known unchanged
  source incident is observability evidence, not a recurring manual assignment.
- Manual workflow dispatch remains an emergency control, not a calendar task.

## Human-Action Triggers

Human review begins only when one of these concrete events occurs:

- a public surface cannot represent freshness, provenance, or availability
  truthfully;
- a security, privacy, or data-integrity incident is detected;
- an official source or methodology changes in a way that affects a displayed
  claim;
- automation, dependency, or scheduler failure breaches the documented public
  service contract;
- an explicitly approved release or data-flow change requires its existing
  release, privacy, documentation, or rollback checks.

Each response is limited to the affected contract. Stop when truthfulness is
restored, the source is narrowed or suspended, or the concrete incident is
otherwise contained.

## Parked Historical Material

- The [trusted source-freshness offload pilot](../operations/heartbeat-offload-pilot.md)
  is an inactive reference, not an external-operations queue.
- Ontario representation remains documented as a known limitation. It is not a
  standing methods task and must not be used to restart research activity.
- Public-health additions, new provinces, scheduling experiments, and other
  expansion candidates remain inactive historical planning material.
- The completed option-value screen and its reactivation gate are preserved in
  the [closeout record](archive/maintenance-2026-08-15-option-value-screen-closeout.md).

## Triggered-Response Checklist

- Emergency and non-triage disclaimers remain prominent.
- Methodology caveats are not weakened.
- Public docs avoid private hostnames, paths, credentials, runbooks, and
  personal strategy notes.
- Source attribution links point to official provincial or federal sources.
- Durable private project notes live in the private/shared operations source
  of truth; ignored `private/` folders may exist locally only as convenience
  copies.
- Actual secrets remain in Bitwarden or deployment environments, not Git.
