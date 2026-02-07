"""Tests for region mapping audit/auto-assignment CLI."""

from pathlib import Path
from unittest.mock import Mock, patch

from waittime.cli.region_mapping import (
    assign_region_code,
    auto_assign_regions,
    build_coverage_report,
    load_overrides,
    main,
)
from waittime.core import Hospital


def make_hospital(
    hospital_id: str,
    name: str,
    city: str,
    latitude: float,
    longitude: float,
) -> Hospital:
    """Create a valid hospital model for tests."""
    return Hospital(
        id=hospital_id,
        name=name,
        province="ON",
        city=city,
        latitude=latitude,
        longitude=longitude,
        is_verified=True,
        is_visible=True,
        source_id="ontario-health",
    )


def test_load_overrides_missing_file_returns_empty() -> None:
    """Missing overrides file should not fail."""
    overrides = load_overrides(Path("does-not-exist.json"))
    assert overrides == {}


def test_load_overrides_reads_mappings(tmp_path: Path) -> None:
    """Overrides should normalize region codes to uppercase."""
    file_path = tmp_path / "overrides.json"
    file_path.write_text(
        '{"mappings":{"ca-on-test":"east","ca-on-test-2":"toronto"}}',
        encoding="utf-8",
    )

    overrides = load_overrides(file_path)

    assert overrides["ca-on-test"] == "EAST"
    assert overrides["ca-on-test-2"] == "TORONTO"


def test_assign_region_code_uses_override() -> None:
    """Overrides take precedence over heuristics."""
    hospital = make_hospital("ca-on-test", "X", "Somewhere", 43.7, -79.4)
    code, reason = assign_region_code(hospital, {"ca-on-test": "NORTH"})
    assert code == "NORTH"
    assert reason == "override"


def test_assign_region_code_token_and_coordinate_fallbacks() -> None:
    """Token and coordinate heuristics should classify expected regions."""
    toronto = make_hospital("h1", "General", "Toronto", 43.7, -79.4)
    north = make_hospital("h2", "Regional", "Unknown", 48.4, -89.2)
    east = make_hospital("h3", "Regional", "Unknown", 44.7, -75.7)
    west = make_hospital("h4", "Regional", "Unknown", 42.9, -81.3)
    central = make_hospital("h5", "Regional", "Unknown", 44.1, -80.4)

    assert assign_region_code(toronto, {})[0] == "TORONTO"
    assert assign_region_code(north, {})[0] == "NORTH"
    assert assign_region_code(east, {})[0] == "EAST"
    assert assign_region_code(west, {})[0] == "WEST"
    assert assign_region_code(central, {})[0] == "CENTRAL"


def test_build_coverage_report_counts_mapped_and_unmapped() -> None:
    """Coverage report should summarize mapping counts correctly."""
    hospitals = [
        make_hospital("h1", "A", "Toronto", 43.7, -79.4),
        make_hospital("h2", "B", "Ottawa", 45.4, -75.7),
        make_hospital("h3", "C", "London", 42.9, -81.2),
    ]
    mappings = [
        {"hospital_id": "h1", "region_id": "r-toronto"},
        {"hospital_id": "h2", "region_id": "r-east"},
    ]
    regions = [
        {"id": "r-toronto", "code": "TORONTO"},
        {"id": "r-east", "code": "EAST"},
    ]

    report = build_coverage_report(hospitals, mappings, regions)

    assert report["total_hospitals"] == 3
    assert report["mapped_hospitals"] == 2
    assert report["unmapped_hospitals"] == 1
    assert report["coverage_percent"] == 66.7
    assert report["region_counts"]["TORONTO"] == 1
    assert report["region_counts"]["EAST"] == 1
    assert report["unmapped_ids"] == ["h3"]


def test_auto_assign_regions_assigns_only_unmapped_by_default() -> None:
    """Auto-assign should skip already-mapped rows unless remap_all is set."""
    db = Mock()
    db.list_regions.return_value = [
        {"id": "r-east", "code": "EAST"},
        {"id": "r-toronto", "code": "TORONTO"},
        {"id": "r-central", "code": "CENTRAL"},
        {"id": "r-west", "code": "WEST"},
        {"id": "r-north", "code": "NORTH"},
    ]
    db.list_hospitals.return_value = [
        make_hospital("h1", "A", "Toronto", 43.7, -79.4),
        make_hospital("h2", "B", "Ottawa", 45.4, -75.7),
    ]
    db.list_hospital_regions.return_value = [{"hospital_id": "h1", "region_id": "r-toronto"}]

    result = auto_assign_regions(db, province="ON", overrides={}, dry_run=False, remap_all=False)

    assert result["assigned"] == 1
    assert result["skipped_existing"] == 1
    db.upsert_hospital_region.assert_called_once()


def test_auto_assign_regions_dry_run_does_not_write() -> None:
    """Dry run should not write assignments."""
    db = Mock()
    db.list_regions.return_value = [
        {"id": "r-east", "code": "EAST"},
        {"id": "r-toronto", "code": "TORONTO"},
        {"id": "r-central", "code": "CENTRAL"},
        {"id": "r-west", "code": "WEST"},
        {"id": "r-north", "code": "NORTH"},
    ]
    db.list_hospitals.return_value = [make_hospital("h2", "B", "Ottawa", 45.4, -75.7)]
    db.list_hospital_regions.return_value = []

    result = auto_assign_regions(db, province="ON", overrides={}, dry_run=True, remap_all=False)

    assert result["assigned"] == 1
    db.upsert_hospital_region.assert_not_called()


def test_main_writes_json_report(tmp_path: Path) -> None:
    """Main should support writing report JSON payload."""
    output_file = tmp_path / "report.json"

    mock_db = Mock()
    mock_db.list_hospitals.return_value = [make_hospital("h1", "A", "Toronto", 43.7, -79.4)]
    mock_db.list_hospital_regions.return_value = [{"hospital_id": "h1", "region_id": "r-toronto"}]
    mock_db.list_regions.return_value = [{"id": "r-toronto", "code": "TORONTO"}]

    with (
        patch("sys.argv", ["region_mapping.py", "--output-json", str(output_file)]),
        patch("waittime.cli.region_mapping.DatabaseService", return_value=mock_db),
    ):
        code = main()

    assert code == 0
    assert output_file.exists()
