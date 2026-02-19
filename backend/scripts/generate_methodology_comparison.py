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

import csv
from datetime import datetime
from pathlib import Path


def main() -> None:
    """Generate methodology comparison matrices."""
    # Define project root (script is in backend/scripts/)
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "docs" / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Provincial methodology data
    # Source: backend/docs/methodologies/README.md (lines 49-55)
    provinces = [
        {
            "province": "Ontario",
            "province_code": "ON",
            "source_id": "ontario-health",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "POINT_ESTIMATE",
            "metric_family": "TIME_TO_PROVIDER",
            "update_frequency": "~15 min",
            "data_source": "Ontario Health (ER Watch)",
            "notes": "Real-time instantaneous wait times",
        },
        {
            "province": "Alberta",
            "province_code": "AB",
            "source_id": "alberta-ahs",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "POINT_ESTIMATE",
            "metric_family": "TIME_TO_PROVIDER",
            "update_frequency": "~2 min",
            "data_source": "Alberta Health Services (AHS) Wait Times Portal",
            "notes": "Real-time instantaneous wait times, fastest update frequency",
        },
        {
            "province": "British Columbia",
            "province_code": "BC",
            "source_id": "bc-phsa",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "P90",
            "metric_family": "TIME_TO_PROVIDER",
            "update_frequency": "~5 min",
            "data_source": "BC PHSA (edwaittimes.ca)",
            "notes": "90th percentile statistic, not directly comparable to real-time estimates",
        },
        {
            "province": "Quebec",
            "province_code": "QC",
            "source_id": "quebec-msss",
            "start_event": "REGISTRATION",
            "end_event": "PHYSICIAN",
            "statistic_type": "ROLLING_AVG",
            "metric_family": "TIME_TO_PROVIDER",
            "update_frequency": "Periodic",
            "data_source": "MSSS Emergency Room Situation Portal",
            "notes": "Uses REGISTRATION (not TRIAGE) start event; rolling average statistic; incomparable to all other provinces on two ontology dimensions",
        },
    ]

    # Pairwise comparability data
    # Source: backend/docs/methodologies/README.md (lines 58-66)
    pairwise = [
        {
            "province_a": "Ontario",
            "province_b": "Alberta",
            "comparable": "Partial",
            "divergent_fields": "statistic_type matches (both POINT_ESTIMATE)",
            "notes": "Same ontology when using real-time Ontario data. Most comparable pair.",
        },
        {
            "province_a": "Ontario",
            "province_b": "BC",
            "comparable": "No",
            "divergent_fields": "statistic_type (POINT_ESTIMATE vs P90)",
            "notes": "Same start/end events but different statistics. P90 systematically higher.",
        },
        {
            "province_a": "Ontario",
            "province_b": "Quebec",
            "comparable": "No",
            "divergent_fields": "start_event + statistic_type",
            "notes": "Two dimensions differ. Quebec times systematically higher due to REGISTRATION start.",
        },
        {
            "province_a": "Alberta",
            "province_b": "BC",
            "comparable": "No",
            "divergent_fields": "statistic_type (POINT_ESTIMATE vs P90)",
            "notes": "Same start/end events but different statistics. P90 systematically higher.",
        },
        {
            "province_a": "Alberta",
            "province_b": "Quebec",
            "comparable": "No",
            "divergent_fields": "start_event + statistic_type",
            "notes": "Two dimensions differ. Quebec most distinct methodology.",
        },
        {
            "province_a": "BC",
            "province_b": "Quebec",
            "comparable": "No",
            "divergent_fields": "start_event + statistic_type",
            "notes": "Two dimensions differ. Quebec most distinct methodology.",
        },
    ]

    # Generate main comparison CSV
    csv_path = output_dir / "methodology-comparison.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "province",
                "province_code",
                "source_id",
                "metric_family",
                "start_event",
                "end_event",
                "statistic_type",
                "update_frequency",
                "data_source",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(provinces)

    print(f"✓ Generated: {csv_path}")

    # Generate main comparison HTML
    html_path = output_dir / "methodology-comparison.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_main_html(provinces))

    print(f"✓ Generated: {html_path}")

    # Generate pairwise comparability CSV
    pairwise_csv_path = output_dir / "methodology-pairwise-comparability.csv"
    with open(pairwise_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "province_a",
                "province_b",
                "comparable",
                "divergent_fields",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(pairwise)

    print(f"✓ Generated: {pairwise_csv_path}")

    # Generate pairwise comparability HTML
    pairwise_html_path = output_dir / "methodology-pairwise-comparability.html"
    with open(pairwise_html_path, "w", encoding="utf-8") as f:
        f.write(generate_pairwise_html(pairwise))

    print(f"✓ Generated: {pairwise_html_path}")

    print("\n✅ All methodology comparison assets generated successfully!")
    print(f"\nOutput directory: {output_dir}")


def generate_main_html(provinces: list[dict]) -> str:
    """Generate HTML table for main methodology comparison."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wait Time Canada - Provincial Methodology Comparison</title>
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
        <h1>🏥 Provincial Emergency Department Wait Time Methodology Comparison</h1>
        <div class="metadata">
            <strong>Wait Time Canada</strong> - Health Systems Observatory<br>
            Generated: {timestamp}<br>
            Provinces: Ontario, Alberta, British Columbia, Quebec<br>
            Source: <a href="https://github.com/jerdaw/waittimecanada">github.com/jerdaw/waittimecanada</a>
        </div>

        <div class="warning">
            <strong>⚠️ Comparability Warning:</strong> Direct comparison of wait times across provinces
            may be scientifically invalid due to methodological differences. Always consider
            start_event, end_event, and statistic_type when interpreting cross-province data.
        </div>

        <table>
            <thead>
                <tr>
                    <th>Province</th>
                    <th>Source ID</th>
                    <th>Start Event</th>
                    <th>End Event</th>
                    <th>Statistic Type</th>
                    <th>Update Frequency</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
"""

    for p in provinces:
        html += f"""                <tr>
                    <td><span class="province-code">{p['province_code']}</span> {p['province']}</td>
                    <td><code>{p['source_id']}</code></td>
                    <td><span class="ontology-field">{p['start_event']}</span></td>
                    <td><span class="ontology-field">{p['end_event']}</span></td>
                    <td><span class="ontology-field">{p['statistic_type']}</span></td>
                    <td>{p['update_frequency']}</td>
                    <td>{p['notes']}</td>
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
                <td>When the wait time clock starts</td>
                <td>TRIAGE starts after clinical assessment; REGISTRATION starts after administrative check-in (earlier)</td>
            </tr>
            <tr>
                <td><span class="ontology-field">END_EVENT</span></td>
                <td>When the wait time clock stops</td>
                <td>PHYSICIAN = first physician assessment (standard across all provinces)</td>
            </tr>
            <tr>
                <td><span class="ontology-field">STATISTIC_TYPE</span></td>
                <td>How the value is calculated</td>
                <td>POINT_ESTIMATE = current/instantaneous; P90 = 90th percentile; ROLLING_AVG = moving average</td>
            </tr>
        </table>

        <div class="footer">
            <strong>Citation:</strong><br>
            Wait Time Canada. (2026). Provincial Emergency Department Wait Time Methodology Comparison.
            Retrieved from https://github.com/jerdaw/waittimecanada<br><br>

            <strong>License:</strong> MIT License<br>
            <strong>Contact:</strong> See repository for details
        </div>
    </div>
</body>
</html>
"""

    return html


def generate_pairwise_html(pairwise: list[dict]) -> str:
    """Generate HTML table for pairwise comparability analysis."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wait Time Canada - Pairwise Comparability Matrix</title>
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
        <h1>🔍 Pairwise Province Comparability Matrix</h1>
        <div class="metadata">
            <strong>Wait Time Canada</strong> - Health Systems Observatory<br>
            Generated: {timestamp}<br>
            Comparisons: 6 pairwise combinations (4 provinces)<br>
            Source: <a href="https://github.com/jerdaw/waittimecanada">github.com/jerdaw/waittimecanada</a>
        </div>

        <div class="key-finding">
            <strong>🔬 Key Finding:</strong> No province pair is fully comparable. Ontario and Alberta share
            the closest methodology (both TRIAGE → PHYSICIAN, POINT_ESTIMATE), but even these represent
            instantaneous snapshots that may vary by measurement timing. <strong>Quebec is the most
            methodologically distinct province.</strong>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Province A</th>
                    <th>Province B</th>
                    <th>Comparable?</th>
                    <th>Divergent Fields</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
"""

    for pw in pairwise:
        comparable_class = {
            "Yes": "comparable-yes",
            "No": "comparable-no",
            "Partial": "comparable-partial",
        }[pw["comparable"]]

        html += f"""                <tr>
                    <td><strong>{pw['province_a']}</strong></td>
                    <td><strong>{pw['province_b']}</strong></td>
                    <td><span class="{comparable_class}">{pw['comparable']}</span></td>
                    <td>{pw['divergent_fields']}</td>
                    <td>{pw['notes']}</td>
                </tr>
"""

    html += """            </tbody>
        </table>

        <h2>📊 Comparability Criteria</h2>
        <p>Two measurements are <strong>directly comparable</strong> if and only if:</p>
        <pre style="background: #ecf0f1; padding: 15px; border-radius: 4px; overflow-x: auto;">comparable = (
    measurement_a.metric_family == measurement_b.metric_family AND
    measurement_a.start_event == measurement_b.start_event AND
    measurement_a.end_event == measurement_b.end_event AND
    measurement_a.statistic_type == measurement_b.statistic_type
)</pre>
        <p>If any dimension differs, a <strong>divergence brief</strong> must be generated explaining
        why direct comparison is scientifically invalid.</p>

        <div class="footer">
            <strong>Citation:</strong><br>
            Wait Time Canada. (2026). Provincial Emergency Department Wait Time Pairwise Comparability Matrix.
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
