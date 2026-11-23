# Quebec Emergency Department Wait Time Methodology

> [!WARNING]
> **Quebec methodology revalidation required.** An audit of official sources on
> 22 Nov 2026 found no official text that supports the repository's Quebec tags
> (`REGISTRATION -> PHYSICIAN`, `ROLLING_AVG`, `patient_scope: ALL`). The stored
> tags are legacy implementation values pending an ontology and
> historical-data decision. Until that decision is made, do not treat them as
> a transcription of Quebec's definition, and do not backfill or reinterpret
> historical Quebec values.
>
> What the official sources say (all accessed 22 Nov 2026):
>
> - The quebec.ca page "Situation in emergency rooms in Quebec" labels the
>   figure "Estimated waiting time for non-priority cases to see a doctor".
>   Its only footnote says the estimate "is based on the clientele who arrive
>   in the emergency department waiting room". The page states no start point,
>   statistic, averaging window, or definition of "non-priority". The words
>   "registration" and "rolling average" do not appear in the page's text.
>   <https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec>
> - Quebec's retrospective products are different from the live estimate. The
>   cumulative open-data file's variable list (dated 15 Dec 2023) measures the
>   delay from the end of the first triage to first medical care by a
>   physician, as a mean, and excludes patients who left before being seen.
>   <https://www.donneesquebec.ca/recherche/dataset/b7e297c3-ff0f-4e11-bc0f-2add3cffdd76>
> - The public performance dashboard notes define a seven-day moving average of
>   the delay from the first triage to the physician, and state that the time
>   from arrival to the end of triage is not included.
>   <https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/performance-reseau-sante-services-sociaux>
> - The hourly open-data file (Donnees Quebec, "Fichier horaire des donnees de
>   la situation a l'urgence") has no variable for the estimated waiting time.
>   <https://donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence>
>
> No official page links the live estimate to either retrospective measure, so
> it is unknown whether they are the same quantity.

## Executive Summary

Quebec reports an estimated waiting time for non-priority cases through the
Ministere de la Sante et des Services sociaux (MSSS) web portal. The portal
does not publish how that figure is defined.

**Key Findings:**
- The live figure's start point, statistic, averaging window, and patient scope
  are **not published**. The repository's `REGISTRATION` and `ROLLING_AVG`
  tags are legacy implementation values with no official support.
- The patient scope is described by the publisher only as "non-priority
  cases"; the priority levels it covers are not stated. The earlier claim that
  the figure covers all acuity levels has no source and is withdrawn.
- Quebec's retrospective products start at the end of the first triage, not at
  registration (see the warning above).
- Data covers 110+ emergency departments across Quebec health regions.
- Because the live definition is unpublished, any comparison with another
  province must be labelled "definition not published by the publisher", not
  as a registration-versus-triage difference.

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Metric Ontology](#metric-ontology)
3. [Comparability Analysis](#comparability-analysis)
4. [Technical Implementation](#technical-implementation)
5. [Policy Context](#policy-context)
6. [References](#references)

---

## Data Sources

### Primary Source: MSSS Emergency Room Situation Portal

**Provider:** Ministere de la Sante et des Services sociaux (MSSS)
**URL:** https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec
**Coverage:** 110+ emergency departments across Quebec
**Update Frequency:** The page shows a "last update" timestamp; the hourly open-data file is extracted every hour (exact refresh of the estimate not documented)
**Data Type:** Estimate; method not published

**What They Report:**
- **Estimated waiting time for non-priority cases to see a doctor**: scraped. Start point, statistic, and window are not published.
- **Stretcher occupancy rate**: Percentage of stretchers in use. Scraped (M17) and stored as STRETCHER_OCCUPANCY measurements. The percentage is not defined in the open-data dictionary.
- **Number of people waiting to see a doctor**: displayed, not scraped.
- **Average length of stay in the waiting room (previous day)**: displayed, not scraped.

**What the official sources do not say:** where the clock starts, what
statistic is reported (mean, median, model output), any averaging window, which
priority levels count as "non-priority", or how patients who leave without being
seen are treated.

**Ontology Mapping (Wait Time), legacy implementation tags only:**
```
metric_family: TIME_TO_PROVIDER
start_event: REGISTRATION     # unsupported by official text
end_event: PHYSICIAN
statistic_type: ROLLING_AVG   # unsupported by official text
patient_scope: ALL            # unsupported; publisher says "non-priority cases"
mapping_status: LEGACY_IMPLEMENTATION_TAGS_PENDING_REVALIDATION
```

This block documents current stored behavior only. It is not the recommended
mapping. The existing ontology has no value for "start point not published".
`UNKNOWN` exists for `start_event`, but changing tags is a code, ontology, and
historical-data decision that is outside this documentation correction.

**Ontology Mapping (Occupancy), legacy implementation tags:**
```
metric_family: STRETCHER_OCCUPANCY
start_event: UNKNOWN (point-in-time snapshot)
end_event: PHYSICIAN (placeholder for consistency)
statistic_type: POINT_ESTIMATE
patient_scope: ALL
```

The occupancy tags were not part of the 22 Nov 2026 audit finding and are
unchanged.

**Note:** Stretcher occupancy is reported as a percentage (e.g., 110% = 10% over capacity). This is a **Quebec-only metric** - no other province currently reports occupancy data.

---

## Metric Ontology

### Time-to-Provider: what is and is not known

**Start event: not published for the live estimate.**
- The repository stores `REGISTRATION`. No official Quebec text says the live
  estimate starts at registration.
- The only official Quebec definitions (retrospective products) start at the
  end of the first triage and exclude the arrival-to-triage interval. That is
  the opposite of a registration start.
- The MSSS dashboard notes also warn that length-of-stay start times vary by
  facility (some use arrival, others the start of first triage).

**End event: a doctor.** The live label says "to see a doctor". The stored
`PHYSICIAN` tag is consistent with that wording.

**Statistic: not published.**
- The repository stores `ROLLING_AVG`. "Rolling average" does not appear in
  the live page. A seven-day moving average does exist, but it belongs to the
  retrospective dashboard, not to the live estimate.
- The footnote says the figure "can vary quickly" and "may not reflect
  reality", which suggests a current-state estimate. That is a reading of the
  footnote, not a published definition.

**Patient scope: "non-priority cases", priority levels not stated.**

**Key Distinction:**
Because the live definition is unpublished, the repository cannot say whether
Quebec's number is longer or shorter than another province's for the same
patient flow. Earlier statements that registration adds a fixed interval to
Quebec's figures, or that Quebec's numbers systematically appear longer, are
withdrawn: no source supports them.

---

## Comparability Analysis

### Cross-Province Comparisons

The safe conclusion is unchanged: direct comparison between Quebec and any
other province is not supported. The reason is now that Quebec's live
definition is not published, so event boundaries and statistic cannot be
matched to anything. The stored tags differ from the other provinces' tags, but
that difference reflects legacy implementation values, not a verified
difference in what the sources measure.

**Quebec vs Ontario:** Not comparable. Ontario's official indicator is a
monthly mean from the earlier of triage or registration to first assessment
(see the Ontario methodology note); Quebec's live estimate has no published
definition.

**Quebec vs BC:** Not comparable. BC publishes a 90th-percentile time from
triage assessment to seeing a physician or nurse practitioner; Quebec's
statistic is unpublished.

**Quebec vs Alberta:** Not comparable. Alberta publishes a software-modelled
estimate for a mid-acuity patient from triage nurse assessment to physician;
Quebec's method is unpublished.

### Safe Divergence Brief

> **Methodology Divergence**
> **Quebec (MSSS)** publishes an estimated waiting time for non-priority cases
> to see a doctor, with no published start point, statistic, or window.
> **The other province's source** publishes its own documented definition.
>
> **Why this matters:**
> - The two figures cannot be shown to measure the same interval.
> - **Direct comparison is invalid.** Do not infer that either number is
>   higher or lower because of where the clock starts.

---

## Technical Implementation

### Scraper Configuration

```python
SOURCE = Source(
    id="quebec-msss",
    name="Ministere de la Sante et des Services sociaux",
    province="QC",
    url="https://www.quebec.ca/en/health/...",
    methodology_url=None,  # no official definition of the live estimate
    telehealth_name="Info-Sante 811",
    telehealth_number="811",
    default_metric_family=MetricFamily.TIME_TO_PROVIDER,
    default_start_event=StartEvent.REGISTRATION,  # legacy tag, pending revalidation
    default_end_event=EndEvent.PHYSICIAN,
    default_statistic_type=StatisticType.ROLLING_AVG,  # legacy tag, pending revalidation
)
```

The three tag defaults above are legacy implementation values (see the warning
at the top of this document).

### Scraper Approach: Paginated AJAX

**Why Pagination is Needed:**
- The MSSS portal uses a Typo3 AJAX endpoint with paginated results
- Results are returned as HTML fragments (10 hospitals per page)
- Typically 12+ pages covering 110+ hospitals

**Implementation:**
1. Iterate through pages using the Typo3 AJAX endpoint
2. Parse HTML fragments for `div.hospital_element` cards
3. Extract hospital name and wait time from each card
4. Handle bilingual content (French and English text patterns)
5. Respect 1-second delay between page requests

### Hospital ID Generation

Quebec uses a two-tier ID system:
1. **Static mapping** for well-known hospitals (21 entries in `HOSPITAL_MAPPING`)
2. **Auto-generation** via NFKD normalization for newly discovered hospitals

```python
# Static mapping examples:
"CHUM" -> "ca-qc-chum"
"Hopital general juif" -> "ca-qc-jewish-general"

# Auto-generated examples:
"Hopital de Gatineau" -> "ca-qc-hopital-de-gatineau"
"CHU Sainte-Justine" -> "ca-qc-chu-sainte-justine"
```

### Wait Time Parsing

Quebec reports wait times in multiple formats:
- `"4 h 15 min"` (hours and minutes, French style)
- `"2:30"` (time format)
- `"120 min"` (minutes only)

The parser handles all variants and converts to total minutes.

---

## Policy Context

### Info-Sante 811

Quebec's telehealth service:
- **Phone:** 811
- **Service:** Info-Sante 811 provides 24/7 telephone nursing consultation
- **Languages:** French, English, and interpretation services
- **Scope:** Health advice, referral guidance, non-emergency triage

**Integration:**
> When displaying Quebec hospital data, show:
> "Before visiting an emergency department, consider calling Info-Sante 811 for health advice."

### Quebec Health Network Structure

Quebec's health system is organized into regional CISSS/CIUSSS:

| Region | Key Facilities |
|--------|---------------|
| **Montreal** | CHUM, Jewish General, Maisonneuve-Rosemont, Sacre-Coeur, Notre-Dame, Santa Cabrini |
| **Laval** | Hopital de la Cite-de-la-Sante |
| **Monteregie** | Charles-Le Moyne, Pierre-Boucher, Anna-Laberge, Haut-Richelieu, Honore-Mercier |
| **Quebec City** | CHU de Quebec (Enfant-Jesus, CHUL, Hotel-Dieu) |
| **Outaouais** | Hopital de Gatineau, Hopital de Hull |

### Outaouais-Ottawa Corridor

The Gatineau/Hull hospitals are particularly important for the Wait Time Canada cross-province comparison narrative:
- **Hopital de Gatineau** is 15 km from **The Ottawa Hospital - Civic Campus**
- These facilities serve overlapping populations in the National Capital Region
- Despite geographic proximity, their methodologies are completely incomparable
- This demonstrates why methodology transparency matters for patient decision-making

### Triage System (ETG / CTAS)

Quebec uses the Echelle de triage et de gravite (ETG), the French-language adaptation of CTAS:
1. **P1 (Reanimation)**: Immediate
2. **P2 (Tres urgent)**: 15 minutes
3. **P3 (Urgent)**: 30 minutes
4. **P4 (Moins urgent)**: 60 minutes
5. **P5 (Non urgent)**: 120 minutes

The portal labels its estimate as being for **non-priority cases**. It does not say which priority levels that covers, so the stored `patient_scope: ALL` is not supported by the official text.

---

## Geographic Coverage

### Current Coverage

Quebec has the broadest coverage of any province in our system with **110+ emergency departments** across all health regions, including:

- **Major urban centres**: Montreal, Quebec City, Laval, Longueuil, Gatineau
- **Regional hospitals**: Rimouski, Chicoutimi, Sherbrooke, Trois-Rivieres
- **Community hospitals**: Smaller facilities across rural Quebec

### Notable Coverage

Unlike BC (which only covers Vancouver Coastal/Fraser regions), Quebec's MSSS portal covers the **entire province**, making it the most comprehensive provincial data source by geographic coverage.

---

## Validation Checklist

When adding a new Quebec hospital measurement:

- [ ] Hospital ID follows format `ca-qc-{normalized-slug}`
- [ ] `source_id` is `quebec-msss`
- [ ] `metric_family` is `TIME_TO_PROVIDER`
- [ ] `start_event` matches the stored legacy default (`REGISTRATION`; unsupported by official text, pending revalidation)
- [ ] `end_event` is `PHYSICIAN`
- [ ] `statistic_type` matches the stored legacy default (`ROLLING_AVG`; pending revalidation)
- [ ] `patient_scope` matches the stored legacy default (`ALL`; the publisher says "non-priority cases"; pending revalidation)
- [ ] Timestamp is in UTC
- [ ] Raw payload is hashed (not stored in full)

---

## References

### Official Documentation

1. **MSSS - Situation in Emergency Rooms**
   https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec

2. **Quebec Health System Organization**
   https://www.quebec.ca/en/health/health-system-and-services/service-organization

3. **Donnees Quebec - Fichier horaire des donnees de la situation a l'urgence** (no variable for the estimated waiting time; accessed 22 Nov 2026)
   https://donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence

4. **Donnees Quebec - Fichier des donnees cumulatives a l'urgence** (retrospective; first triage to physician; accessed 22 Nov 2026)
   https://www.donneesquebec.ca/recherche/dataset/b7e297c3-ff0f-4e11-bc0f-2add3cffdd76

5. **Quebec.ca - Performance du reseau (dashboard notes; accessed 22 Nov 2026)**
   https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/performance-reseau-sante-services-sociaux

6. **Canadian Triage and Acuity Scale (CTAS/ETG)**
   https://caep.ca/wp-content/uploads/2017/06/module_1_slides_v2.5_2012.pdf

### Telehealth

7. **Info-Sante 811**
   https://www.quebec.ca/en/health/finding-a-resource/info-sante-811

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial methodology documentation |
| 1.1 | 2026-11-22 | Revalidation warning; removed unsupported registration, rolling-average, all-acuity, and 15-60 minute claims |

---

*Last Updated: November 22, 2026*
*Maintained by: Wait Time Canada Research Team*
