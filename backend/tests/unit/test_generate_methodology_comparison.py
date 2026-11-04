from scripts.generate_methodology_comparison import (
    PROVINCE_METADATA,
    build_pairwise_rows,
    build_province_rows,
    generate_main_html,
    generate_pairwise_html,
    load_source_catalog,
)
from waittime.core import Source


def test_build_province_rows_uses_catalog_tags_and_curated_scope_evidence():
    """Rows separate seed tags from the curated source-scope evidence."""
    catalog = load_source_catalog()

    provinces = build_province_rows(catalog)
    by_source_id = {province["source_id"]: province for province in provinces}

    assert by_source_id["ontario-health"]["data_source"] == "Health Quality Ontario"
    assert by_source_id["ontario-health"]["statistic_type"] == "MEAN"
    assert by_source_id["ontario-health"]["patient_scope"] == "ALL"
    assert by_source_id["ontario-health"]["tag_basis"] == "Documented source mapping"
    assert by_source_id["alberta-ahs"]["statistic_type"] == "POINT_ESTIMATE"
    assert by_source_id["alberta-ahs"]["patient_scope"] == "ALL"
    assert by_source_id["bc-phsa"]["patient_scope"] == "ALL"
    assert by_source_id["quebec-msss"]["patient_scope"] == "NON_PRIORITY"
    assert "legacy and unverified" in by_source_id["quebec-msss"]["tag_basis"]
    assert "does not confirm" in by_source_id["quebec-msss"]["notes"]


def test_patient_scope_evidence_does_not_extend_source_seed_contract():
    catalog = load_source_catalog()
    assert all("default_patient_scope" not in source for source in catalog.values())
    assert "default_patient_scope" not in Source.model_fields


def test_missing_curated_scope_is_reported_as_unknown(monkeypatch):
    catalog = load_source_catalog()
    monkeypatch.setitem(PROVINCE_METADATA["quebec-msss"], "patient_scope", "")

    provinces = build_province_rows(catalog)
    quebec = next(row for row in provinces if row["source_id"] == "quebec-msss")

    assert quebec["patient_scope"] == "UNKNOWN"


def test_build_pairwise_rows_reflects_ontario_mean_vs_alberta_point_estimate():
    """Ontario and Alberta should remain partial because only statistic_type differs."""
    catalog = load_source_catalog()
    provinces = build_province_rows(catalog)

    pairwise = build_pairwise_rows(provinces)
    ontario_alberta = next(
        row for row in pairwise if row["province_a"] == "Ontario" and row["province_b"] == "Alberta"
    )

    assert ontario_alberta["comparable"] == "Partial"
    assert ontario_alberta["divergent_fields"] == "statistic_type (MEAN vs POINT_ESTIMATE)"


def test_unknown_scope_never_counts_as_matching_for_pairwise_comparability():
    left = {
        "province": "Ontario",
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "MEAN",
        "patient_scope": "UNKNOWN",
    }
    right = {**left, "province": "Other province"}

    pair = build_pairwise_rows([left, right])[0]

    assert pair["comparable"] == "Partial"
    assert pair["divergent_fields"] == "patient_scope unknown for one or both sources"
    assert "cannot be established" in pair["notes"]


def test_quebec_pairs_are_not_methodologically_established_from_legacy_tags():
    provinces = build_province_rows(load_source_catalog())

    pairs = build_pairwise_rows(provinces)
    quebec_pairs = [pair for pair in pairs if "Quebec" in (pair["province_a"], pair["province_b"])]

    assert len(quebec_pairs) == 3
    assert all(pair["comparable"] == "Not established" for pair in quebec_pairs)
    assert all("not established" in pair["notes"] for pair in quebec_pairs)


def test_generated_html_distinguishes_scope_evidence_from_legacy_tags():
    provinces = build_province_rows(load_source_catalog())
    pairwise = build_pairwise_rows(provinces)

    main_html = generate_main_html(provinces)
    pairwise_html = generate_pairwise_html(pairwise)

    assert "Published page identifies non-priority cases" in main_html
    assert "other tags are legacy and unverified" in main_html
    assert "Not established" in pairwise_html
    assert "Matching tags are necessary" in pairwise_html
