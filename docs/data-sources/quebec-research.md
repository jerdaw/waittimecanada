# Québec Emergency-Department Data Sources

> Source-contract note for the Québec emergency-room data used by Wait Time
> Canada. Documentation checked 2026-10-22. This is not a live-data validation
> or a claim that an undocumented endpoint is authorized or stable.

## Current Wait-Time Source and Ontology

The active source in this repository is the [Québec.ca situation in emergency
rooms page](https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec).
The implementation in `backend/src/waittime/scrapers/quebec.py` retrieves
paginated page results and parses the displayed wait-time and stretcher
occupancy fields from HTML.

Québec.ca labels the wait-time field “Estimated waiting time for non-priority
cases to see a doctor.” Its note says the estimate is based on the clientele
arriving in the emergency-department waiting room, may vary quickly, and may
not reflect the situation when a person arrives. The page also displays the
current number waiting for medical attention, total people in the emergency
room, stretcher occupancy, and average lengths of stay from the previous day.
The page names the Console provinciale des urgences (CPU); the wait-time note
names the Système d'information et de gestion des urgences as its data source.

The scraper currently records the displayed estimate as
`TIME_TO_PROVIDER`, `REGISTRATION → PHYSICIAN`, `ROLLING_AVG`, with
`patient_scope=ALL` supplied by the `Measurement` model default. This is the
project's existing ontology mapping, documented in
`backend/docs/methodologies/quebec-methodology.md`; the public page does not
publish the estimate's calculation formula or averaging window. Treat those
ontology details as the project's documented interpretation, not as a
CSV-derived fact or a fully specified MSSS statistical method. In particular,
`ALL` conflicts with the published non-priority scope and requires separate
review of producer, comparability, aggregate, and reader behavior; this note
does not relabel stored measurements.

## Official Hourly CSV Publication

MSSS publishes an official [hourly emergency-situation dataset through Données
Québec](https://www.donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence).
The catalog lists two CSV resources and a variable/methodology document:

- [Hourly file resource metadata](https://www.donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence/resource/a9272cc9-8234-40d1-9806-9f6b4c75c20d)
  for `Releve_horaire_urgences_7jours.csv`.
- [Hourly file with number of people resource metadata](https://www.donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence/resource/b256f87f-40ec-4c79-bdba-a23e9c50e741)
  for `Releve_horaire_urgences_7jours_nbpers.csv`.
- [MSSS variable list and methodological
  notes](https://www.donneesquebec.ca/recherche/dataset/d4541afe-9391-44bf-a78f-dae3c9cf1217/resource/968af2e2-8c0f-43d4-9f34-100bd8d295a7/download/listevariables_notesmetho_relevehoraireurgence_20230202.pdf).

The catalog identifies the publisher as MSSS, the resource format as CSV, the
license as CC-BY 4.0, and the update frequency as hourly. The methodology says
the files are derived from the CPU, extracted hourly, and published 45 minutes
later. In the `nbpers` file, the documented fields include total people
present, the count waiting for medical attention, and average ambulatory and
stretcher lengths of stay from the previous day.

The catalog documents those CSV resources and their attribution terms; it does
not specify a request rate limit or availability SLA, or identify a
machine-readable resource for the estimated-wait field. Do not treat the
HTML page implementation as a documented API contract.

These fields are useful but **are not substitutes** for the current
`TIME_TO_PROVIDER` estimate:

| Published field | What it represents | Relationship to current wait-time measurement |
| --- | --- | --- |
| Estimated non-priority wait to see a doctor (Québec.ca page) | The displayed estimated duration described in the page note | Current source field for the project's wait-time measurement |
| Total patients waiting for medical attention (`Nombre_total_de_patients_en_attente_de_PEC`) | A current count of people who have not yet seen a doctor | A count, not a duration; do not convert it to wait minutes |
| Ambulatory/stretcher average length of stay (`DMS_*`) | Arrival-to-departure averages for people who left the previous day | Historical length of stay, not a current estimate of time to first physician assessment |
| Functional/occupied stretcher counts and >24h/>48h counts | Stretcher capacity, occupancy, and long-stay counts | Potential inputs for distinct capacity/occupancy or census reporting; not a wait-time estimate |

The CSV methodology warns that hourly observations can become unrepresentative
when arrivals change quickly and that counts do not reveal staffing or patient
triage priorities. The CSV is therefore a documented machine-readable route
for the fields it defines, but the reviewed documentation does not identify a
CSV/API field for the page's estimated non-priority wait duration, nor does it
document that the estimate can be reconstructed from the CSV fields.

## Observed Empty Responses

Three existing bounded diagnostics on 2026-10-22 recorded HTTP `202`,
`text/html`, and zero response-body bytes for page 1. This records only the
observed response metadata. It does **not** establish why the response was
empty; do not infer a WAF, bot block, or other access-control cause from status
`202` alone. No new collection was run for this source review.

## Bounded Next Source Decision

This review changes neither the active production source nor its current
ontology mapping. The mapping remains open to evidence-based correction
independently of any source change. Any source replacement requires evidence
that the alternative is supported for the exact estimated non-priority wait
field, including its meaning and access/update expectations. If a separate
CSV-backed metric is desired, assess only fields the CSV actually publishes
and preserve their distinct meaning and CC-BY 4.0 attribution. Do not replace
the wait estimate with a waiting count or prior-day length-of-stay average.
For a future source-contract question, the catalog lists
`donnees.ouvertes@msss.gouv.qc.ca` as the MSSS contact; no outreach has been
performed as part of this note.
