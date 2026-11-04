#!/usr/bin/env python3
"""
Generate methodology comparison matrix for cross-province analysis.

This script creates downloadable CSV and HTML assets showing how provincial
emergency department wait time methodologies differ across Canada.

Output files:
    - docs/assets/methodology-comparison.csv
    - docs/assets/methodology-comparison.html
    - docs/assets/methodology-pairwise-comparability.csv
    - docs/assets/methodology-pairwise-comparability.html
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "assets"
SOURCE_DATA_DIR = PROJECT_ROOT / "backend" / "data" / "sources"
ORDERED_SOURCE_IDS = [
    "ontario-health",
    "alberta-ahs",
    "bc-phsa",
    "quebec-msss",
]
COMPARABILITY_FIELDS = [
    "metric_family",
    "start_event",
    "end_event",
    "statistic_type",
    "patient_scope",
]
UNKNOWN_PATIENT_SCOPE = "UNKNOWN"
UNVERIFIED_TAG_BASIS = (
    "Published page confirms patient scope only; other tags are legacy and unverified"
)
PROVINCE_METADATA: dict[str, dict[str, str]] = {
    "ontario-health": {
        "province": "Ontario",
        "province_code": "ON",
        "update_frequency": "Quarterly",
        "data_source": "Health Quality Ontario",
        "patient_scope": "ALL",
        "scope_basis": "Existing project mapping; not independently verified",
        "tag_basis": "Documented source mapping",
        "notes": "Historical mean TRIAGE → PHYSICIAN wait times from Ontario's official performance reporting.",
    },
    "alberta-ahs": {
        "province": "Alberta",
        "province_code": "AB",
        "update_frequency": "~2 min",
        "data_source": "Alberta Health Services Wait Times Portal",
        "patient_scope": "ALL",
        "scope_basis": "Existing project mapping; not independently verified",
        "tag_basis": "Documented source mapping",
        "notes": "Real-time point estimate with the fastest public refresh cadence in the active set.",
    },
    "bc-phsa": {
        "province": "British Columbia",
        "province_code": "BC",
        "update_frequency": "~5 min",
        "data_source": "Provincial Health Services Authority (edwaittimes.ca)",
        "patient_scope": "ALL",
        "scope_basis": "Existing project mapping; not independently verified",
        "tag_basis": "Documented source mapping",
        "notes": "P90 TRIAGE → PHYSICIAN reporting; more conservative than mean or point-estimate displays.",
    },
    "quebec-msss": {
        "province": "Quebec",
        "province_code": "QC",
        "update_frequency": "Periodic",
        "data_source": "MSSS Emergency Room Situation Portal",
        "patient_scope": "NON_PRIORITY",
        "scope_basis": "Published page identifies non-priority cases",
        "tag_basis": UNVERIFIED_TAG_BASIS,
        "notes": "Published page identifies an estimated wait for non-priority cases; it does not confirm the legacy event or statistic tags shown here.",
    },
}


def load_source_catalog() -> dict[str, dict[str, Any]]:
    """Load canonical source definitions from backend/data/sources."""
    catalog: dict[str, dict[str, Any]] = {}

    for source_id in ORDERED_SOURCE_IDS:
        source_path = SOURCE_DATA_DIR / f"{source_id}.json"
        with open(source_path, encoding="utf-8") as source_file:
            catalog[source_id] = json.load(source_file)

    return catalog


def build_province_rows(catalog: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Build rows from registered source tags and curated scope evidence."""
    provinces: list[dict[str, str]] = []

    for source_id in ORDERED_SOURCE_IDS:
        source = catalog[source_id]
        metadata = PROVINCE_METADATA[source_id]
        provinces.append(
            {
                "province": metadata["province"],
                "province_code": metadata["province_code"],
                "source_id": source["id"],
                "metric_family": source["default_metric_family"],
                "start_event": source["default_start_event"],
                "end_event": source["default_end_event"],
                "statistic_type": source["default_statistic_type"],
                "patient_scope": metadata.get("patient_scope") or UNKNOWN_PATIENT_SCOPE,
                "scope_basis": metadata.get("scope_basis", "Not recorded"),
                "tag_basis": metadata["tag_basis"],
                "update_frequency": metadata["update_frequency"],
                "data_source": metadata["data_source"],
                "notes": metadata["notes"],
            }
        )

    return provinces


def build_pairwise_rows(provinces: list[dict[str, str]]) -> list[dict[str, str]]:
    """Build pairwise comparability verdicts from province rows."""
    pairwise: list[dict[str, str]] = []

    for index, left in enumerate(provinces):
        for right in provinces[index + 1 :]:
            differences = [
                field
                for field in COMPARABILITY_FIELDS
                if left[field] != right[field]
                or (
                    field == "patient_scope"
                    and UNKNOWN_PATIENT_SCOPE in (left[field], right[field])
                )
            ]
            match_count = len(COMPARABILITY_FIELDS) - len(differences)

            if any(province.get("tag_basis") == UNVERIFIED_TAG_BASIS for province in (left, right)):
                comparable = "Not established"
            elif not differences:
                comparable = "Yes"
            elif match_count >= 2:
                comparable = "Partial"
            else:
                comparable = "No"

            pairwise.append(
                {
                    "province_a": left["province"],
                    "province_b": right["province"],
                    "comparable": comparable,
                    "divergent_fields": format_divergent_fields(left, right, differences),
                    "notes": build_pairwise_note(left, right, differences),
                }
            )

    return pairwise


def format_divergent_fields(
    left: dict[str, str], right: dict[str, str], differences: list[str]
) -> str:
    """Format a concise divergence summary."""
    if not differences:
        return "none"

    formatted = []
    for field in differences:
        if field == "patient_scope" and UNKNOWN_PATIENT_SCOPE in (
            left[field],
            right[field],
        ):
            formatted.append("patient_scope unknown for one or both sources")
        else:
            formatted.append(f"{field} ({left[field]} vs {right[field]})")
    return "; ".join(formatted)


def build_pairwise_note(left: dict[str, str], right: dict[str, str], differences: list[str]) -> str:
    """Build a human-readable note for pairwise comparisons."""
    if any(province.get("tag_basis") == UNVERIFIED_TAG_BASIS for province in (left, right)):
        return (
            "Compares registered project tags only. The published Québec.ca page confirms "
            "non-priority scope, but not the Québec clock events or statistic; direct "
            "methodological comparability is not established."
        )

    if not differences:
        return "All five registered project tags match; source-method equivalence still requires review."

    if "patient_scope" in differences and UNKNOWN_PATIENT_SCOPE in (
        left["patient_scope"],
        right["patient_scope"],
    ):
        return (
            "Patient scope is unknown for one or both sources, so direct "
            "comparability cannot be established."
        )

    if differences == ["patient_scope"]:
        return (
            "Patient populations differ, so direct comparison is invalid "
            f"({left['patient_scope']} vs {right['patient_scope']})."
        )

    if differences == ["statistic_type"]:
        return (
            "Same metric and event boundaries, but different statistics still block "
            f"direct comparison ({left['statistic_type']} vs {right['statistic_type']})."
        )

    if differences == ["start_event"]:
        return "Clock start definitions differ, so the reported durations are not aligned."

    if "start_event" in differences and "statistic_type" in differences:
        return (
            "Clock start and statistic type both differ, making this one of the least "
            "aligned province pairs."
        )

    return (
        "Multiple ontology dimensions differ, so direct comparison would mix unlike "
        "measurement definitions."
    )


def main() -> None:
    """Generate methodology comparison matrices."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    catalog = load_source_catalog()
    provinces = build_province_rows(catalog)
    pairwise = build_pairwise_rows(provinces)

    csv_path = OUTPUT_DIR / "methodology-comparison.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=[
                "province",
                "province_code",
                "source_id",
                "metric_family",
                "start_event",
                "end_event",
                "statistic_type",
                "patient_scope",
                "scope_basis",
                "tag_basis",
                "update_frequency",
                "data_source",
                "notes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(provinces)

    print(f"✓ Generated: {csv_path}")

    html_path = OUTPUT_DIR / "methodology-comparison.html"
    with open(html_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(generate_main_html(provinces))

    print(f"✓ Generated: {html_path}")

    pairwise_csv_path = OUTPUT_DIR / "methodology-pairwise-comparability.csv"
    with open(pairwise_csv_path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=[
                "province_a",
                "province_b",
                "comparable",
                "divergent_fields",
                "notes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(pairwise)

    print(f"✓ Generated: {pairwise_csv_path}")

    pairwise_html_path = OUTPUT_DIR / "methodology-pairwise-comparability.html"
    with open(pairwise_html_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(generate_pairwise_html(pairwise))

    print(f"✓ Generated: {pairwise_html_path}")

    print("\n✅ All methodology comparison assets generated successfully!")
    print(f"\nOutput directory: {OUTPUT_DIR}")


def generate_main_html(provinces: list[dict[str, str]]) -> str:
    """Generate HTML table for main methodology comparison."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wait Time Canada - Provincial Ontology Tags and Evidence</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .metadata {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .province-code {{
            font-weight: 600;
            color: #2c3e50;
        }}
        .ontology-field {{
            font-family: 'Courier New', monospace;
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Provincial Emergency Department Wait-Time Ontology Tags</h1>
        <div class="metadata">
            <strong>Wait Time Canada</strong> - Health Systems Observatory<br>
            Generated: {timestamp}<br>
            Provinces: Ontario, Alberta, British Columbia, Quebec<br>
            Source: <a href="https://github.com/jerdaw/waittimecanada">github.com/jerdaw/waittimecanada</a>
        </div>

        <div class="warning">
            <strong>⚠️ Comparability Warning:</strong> Direct comparison of wait times across provinces
            may be scientifically invalid due to methodological differences. Always consider
            the registered metric_family, start_event, end_event, statistic_type, and patient_scope tags.
            Québec's published page confirms non-priority scope only; its remaining tags are legacy and unverified.
        </div>

        <table>
            <thead>
                <tr>
                    <th>Province</th>
                    <th>Source ID</th>
                    <th>Metric Family</th>
                    <th>Start Event</th>
                    <th>End Event</th>
                    <th>Statistic Type</th>
                    <th>Patient Scope</th>
                    <th>Scope Evidence</th>
                    <th>Evidence Basis</th>
                    <th>Update Frequency</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
"""

    for province in provinces:
        html += f"""                <tr>
                    <td><span class="province-code">{province["province_code"]}</span> {province["province"]}</td>
                    <td><code>{province["source_id"]}</code></td>
                    <td><span class="ontology-field">{province["metric_family"]}</span></td>
                    <td><span class="ontology-field">{province["start_event"]}</span></td>
                    <td><span class="ontology-field">{province["end_event"]}</span></td>
                    <td><span class="ontology-field">{province["statistic_type"]}</span></td>
                    <td><span class="ontology-field">{province["patient_scope"]}</span></td>
                    <td>{province["scope_basis"]}</td>
                    <td>{province["tag_basis"]}</td>
                    <td>{province["update_frequency"]}</td>
                    <td>{province["notes"]}</td>
                </tr>
"""

    html += """            </tbody>
        </table>

        <h2>📋 Ontology Field Definitions</h2>
        <table>
            <tr>
                <th>Field</th>
                <th>Definition</th>
                <th>Implications</th>
            </tr>
            <tr>
                <td><span class="ontology-field">START_EVENT</span></td>
                <td>The recorded clock-start label</td>
                <td>A tag does not establish the source's operational definition; review source documentation.</td>
            </tr>
            <tr>
                <td><span class="ontology-field">END_EVENT</span></td>
                <td>The recorded clock-end label</td>
                <td>Do not assume identical event semantics across sources from matching labels alone.</td>
            </tr>
            <tr>
                <td><span class="ontology-field">STATISTIC_TYPE</span></td>
                <td>The recorded calculation label</td>
                <td>The source may not publish the calculation details or averaging window; check its documentation.</td>
            </tr>
            <tr>
                <td><span class="ontology-field">PATIENT_SCOPE</span></td>
                <td>Which patient population is included</td>
                <td>Different scopes are not directly comparable; UNKNOWN never counts as a match</td>
            </tr>
        </table>

        <div class="footer">
            <strong>Citation:</strong><br>
            Wait Time Canada. (2026). Provincial Emergency Department Wait-Time Ontology Tags.
            Retrieved from https://github.com/jerdaw/waittimecanada<br><br>

            <strong>License:</strong> MIT License<br>
            <strong>Contact:</strong> See repository for details
        </div>
    </div>
</body>
</html>
"""

    return html


def generate_pairwise_html(pairwise: list[dict[str, str]]) -> str:
    """Generate HTML table for pairwise comparability analysis."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wait Time Canada - Pairwise Ontology-Tag Alignment</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 10px;
        }}
        .metadata {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            background: #e74c3c;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .comparable-yes {{
            background: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .comparable-no {{
            background: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .comparable-partial {{
            background: #fff3cd;
            color: #856404;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .comparable-unknown {{
            background: #e2e3e5;
            color: #343a40;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .key-finding {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Pairwise Ontology-Tag Alignment Matrix</h1>
        <div class="metadata">
            <strong>Wait Time Canada</strong> - Health Systems Observatory<br>
            Generated: {timestamp}<br>
            Comparisons: 6 pairwise combinations (4 provinces)<br>
            Source: <a href="https://github.com/jerdaw/waittimecanada">github.com/jerdaw/waittimecanada</a>
        </div>

        <div class="key-finding">
            <strong>⚠️ Interpretation:</strong> This matrix compares registered project tags, not necessarily
            source-confirmed methods. Québec's published page confirms a non-priority wait estimate but does not
            specify its clock events or statistic; direct methodological comparability involving Québec is not established.
        </div>

        <table>
            <thead>
                <tr>
                    <th>Province A</th>
                    <th>Province B</th>
                    <th>Comparable?</th>
                    <th>Project Tag Differences</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
"""

    for comparison in pairwise:
        comparable_class = {
            "Yes": "comparable-yes",
            "No": "comparable-no",
            "Partial": "comparable-partial",
            "Not established": "comparable-unknown",
        }[comparison["comparable"]]

        html += f"""                <tr>
                    <td><strong>{comparison["province_a"]}</strong></td>
                    <td><strong>{comparison["province_b"]}</strong></td>
                    <td><span class="{comparable_class}">{comparison["comparable"]}</span></td>
                    <td>{comparison["divergent_fields"]}</td>
                    <td>{comparison["notes"]}</td>
                </tr>
"""

    html += """            </tbody>
        </table>

        <p>Rows marked <strong>Not established</strong> contain legacy or incomplete source-method tags.
        Equal project tags alone do not establish that the underlying measures are methodologically equivalent.</p>

        <h2>📊 Recorded-Tag Screening Criteria</h2>
        <p>All five recorded ontology tags must match for the tag-alignment screen to pass:</p>
        <pre style="background: #ecf0f1; padding: 15px; border-radius: 4px; overflow-x: auto;">comparable = (
    measurement_a.metric_family == measurement_b.metric_family AND
    measurement_a.start_event == measurement_b.start_event AND
    measurement_a.end_event == measurement_b.end_event AND
    measurement_a.statistic_type == measurement_b.statistic_type
    AND measurement_a.patient_scope == measurement_b.patient_scope
)</pre>
        <p>Matching tags are necessary but do not prove source methods are identical or a scientific comparison is valid.
        Review source definitions and limitations. Unknown patient scope never counts as a match.</p>

        <div class="footer">
            <strong>Citation:</strong><br>
            Wait Time Canada. (2026). Provincial Emergency Department Ontology-Tag Alignment Matrix.
            Retrieved from https://github.com/jerdaw/waittimecanada<br><br>

            <strong>License:</strong> MIT License<br>
            <strong>Contact:</strong> See repository for details
        </div>
    </div>
</body>
</html>
"""

    return html


if __name__ == "__main__":
    main()
