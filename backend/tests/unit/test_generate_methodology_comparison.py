from scripts.generate_methodology_comparison import (
    build_pairwise_rows,
    build_province_rows,
    load_source_catalog,
)


def test_build_province_rows_uses_canonical_source_catalog():
    """Ontario and Alberta rows should mirror backend/data/sources metadata."""
    catalog = load_source_catalog()

    provinces = build_province_rows(catalog)
    by_source_id = {province["source_id"]: province for province in provinces}

    assert by_source_id["ontario-health"]["data_source"] == "Health Quality Ontario"
    assert by_source_id["ontario-health"]["statistic_type"] == "MEAN"
    assert by_source_id["alberta-ahs"]["statistic_type"] == "POINT_ESTIMATE"


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
