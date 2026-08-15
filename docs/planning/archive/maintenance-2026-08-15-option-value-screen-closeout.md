# Wait Time Canada Option-Value Screen Closeout

**Decision date:** 2026-08-15

**Status:** Closed

**Disposition:** Public-service stewardship and technical portfolio artifact;
no active research, evaluation, or implementation-conversion attempt

## Decision

The bounded option-value screen does not advance Wait Time Canada into a study
or external-validation effort. The project has real technical and
methodological assets, but the current evidence does not establish a reliable
prospective data lane, an independently worthwhile research question, a named
supervisor or operational partner, a ready data or ethics route, or a scheduled
attributable output.

No Wait Time Canada-specific outreach, ontology work, collector repair,
research monitoring, analysis infrastructure, or feature expansion is
authorized by this screen. Essential public-service stewardship remains
event-triggered and should preserve truthful freshness, provenance, security,
and data integrity.

The project may be reconsidered only if an external supervisor or partner
independently identifies a useful fit and the concrete opportunity has all of
the following:

- a named supervisor or accountable partner;
- an independently worthwhile and defensible question;
- a ready data, permissions, and ethics route;
- a bounded role and realistic workload;
- a scheduled report, presentation, manuscript, or evaluated implementation;
- demonstrated capacity without displacing a stronger established project.

Wait Time Canada must not be described as a national performance comparison.

## Evidence Base

### Verified project facts

- The repository contains source- and ontology-tagged raw measurements,
  permanent aggregates, daily data-quality snapshots, source heartbeats, and
  public status routes. This is useful audit infrastructure, not proof that the
  resulting longitudinal data are study-ready.
- The public status contract counts distinct UTC measurement-hour windows and
  explicitly separates that completeness measure from current heartbeat
  freshness.
- The active retention decision keeps a rolling 30-day raw-measurement window;
  older analyses depend on permanent aggregates. Those aggregates preserve
  source and ontology fields, but they cannot recover deleted raw observations
  or retrospectively correct unmodelled collection gaps.
- The four-province methodology draft is already paused. Ontario's official
  composite start and qualifying-provider endpoint do not fit the legacy
  `TRIAGE -> PHYSICIAN` event tags, so the draft cannot support a finalized
  four-province source-level conclusion.
- The bounded continuity screen observed only 62.5% 24-hour
  measurement-hour completeness and a failed Quebec lane, with 21 consecutive
  failures at the screen sample. The later pre-containment release baseline
  recorded Quebec in error with 34 consecutive failures.
- Frontend release `35e06a04aa3efaf0977feee9a910f165f791fb05`
  and its documentation follow-up now fail closed for unhealthy Quebec
  occupancy. Accepted release evidence showed `Cache-Control: no-store` on the
  affected APIs, Quebec occupancy suppressed while other hospital data
  remained available, successful production smoke and documentation checks,
  retained signed rollback, and a clean independent audit.
- The containment changed public presentation, cache behavior, and source
  eligibility. It did not repair the Quebec collector or validate historical
  continuity, source fidelity, missingness assumptions, or study methods.

This closeout reuses the accepted continuity and release evidence. It does not
resample provincial upstream sources or claim that a previously failed
collector remains failed today.

### Important unknowns

- whether any prospective lane has since achieved sustained, interpretable
  completeness;
- whether long-run aggregate gaps and cadence changes can be modelled without
  selection bias;
- whether a supervisor considers the methods contribution independently
  worthwhile;
- whether any institution or independent user has an operational need for the
  platform;
- whether an appropriate permissions or ethics route and feasible student role
  exist;
- whether academic capacity permits this work without displacing a stronger
  externally established opportunity.

These unknowns are not reasons to extend the screen. The negative continuity
finding and absence of external pull already satisfy the stop rules.

## Question Inventory

The inventory below records what the existing system could help investigate;
it is not an active study list. Workload figures are planning ranges, not
completed-work claims.

| Candidate question                                                                                                         | Existing asset                                                                                         | Decisive limitation                                                                                                                        | Minimum plausible project workload                                                           | Disposition                                      |
| -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| How do the public definitions of emergency wait metrics differ across Ontario, Quebec, Alberta, and British Columbia?      | Source methodology records, strict ontology, divergence logic, and a paused draft                      | Ontario is not exactly represented; a documentary comparison does not require the live platform; novelty and supervisory value are unknown | 12-24 hours plus expert review for revalidation, protocol, analysis, and a defensible report | Do not advance without supervisor-defined value  |
| How complete and failure-prone are the project's public-source collection lanes under a prespecified prospective protocol? | Heartbeats, distinct-hour completeness, quality snapshots, and raw 30-day observations                 | The pilot screen was negative; cadence-model changes and missingness require protocol-level treatment before inference                     | 20-40 hours across protocol, observation, quality control, analysis, and output              | Closed unless externally selected and supervised |
| How faithfully does the Quebec occupancy lane reproduce the official source, including missing or suppressed observations? | Occupancy observations, provenance fields, payload hashes/snippets, and fail-closed public eligibility | The collector was failing; full upstream payloads are not retained; no independent validation sample or reviewer exists                    | 12-24 hours plus an agreed validation sample and reviewer                                    | Closed unless externally selected and supervised |
| Does the observatory improve interpretation or operational use for an independent organization?                            | Public methods, APIs, divergence warnings, and a deployed service                                      | No verified independent workflow, partner, user cohort, or outcome measure is present                                                      | Not estimable until a partner defines the workflow; necessarily exceeds the option screen    | Not currently evaluable                          |

None of these questions supports a national performance comparison or a claim
about hospital or provincial quality.

## Gate and Stop-Rule Evaluation

| Gate or stop rule                         | Result               | Consequence                                                                               |
| ----------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------- |
| Sustained, interpretable continuity       | **Not met**          | The prior screen's negative continuity evidence closes the preservation hypothesis        |
| Independently worthwhile question         | **Not met**          | Existing questions remain founder-originated possibilities, not validated study questions |
| Named supervisor or partner               | **Not met**          | No project-specific outreach is justified after a negative data screen                    |
| Ready data, permissions, and ethics route | **Not met**          | Raw retention, aggregate gaps, and source-fidelity requirements remain unresolved         |
| Bounded role and feasible capacity        | **Not demonstrated** | Do not consume academic capacity to test a path that has already missed earlier gates     |
| Scheduled attributable output             | **Not met**          | There is no protocol, review schedule, or output commitment                               |
| Superior established opportunity          | **Unknown**          | An established externally supervised opportunity continues to win a tie                   |
| Screen budget                             | **Not breached**     | Closure is by evidence, not exhaustion                                                    |

## Screen-Budget Accounting

The option-value ceiling was eight hours. Exact elapsed time was not durably
recorded for the autonomous packets, so this ledger conservatively charges each
completed packet at its approved ceiling:

- continuity/fitness screen: 1.5 hours;
- final evidence reconciliation and closeout: 1.5 hours;
- external consultation, outreach, ontology work, or research setup: 0 hours.

**Total charged: 3.0 of 8.0 hours.** The separate public-truthfulness
containment, release, rollback, and verification work is operational risk
containment and is not charged to the research option screen. The unused five
hours do not roll forward because the screen is closed.

## Operating Disposition

- Keep the live service only within event-triggered, fail-closed stewardship.
- Do not schedule human research monitoring or promise all four source lanes.
- Narrow or suspend a source when truthful freshness, provenance, security, or
  integrity cannot be maintained within the approved operational envelope.
- Preserve the deployed containment tests, public API contract, accepted
  release evidence, methodology warnings, source provenance, and existing
  aggregates.
- Reopen only through the common external-pull gate above, never through
  roadmap momentum or feature expansion.
