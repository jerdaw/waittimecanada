"""Unit tests for Ontario scraper."""

from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from tenacity import RetryError

from waittime.core import EndEvent, MetricFamily, PatientScope, StartEvent, StatisticType
from waittime.scrapers.ontario import OntarioScraper, create_ontario_source


@pytest.mark.unit
class TestOntarioScraper:
    """Tests for Ontario HQOntario scraper."""

    @pytest.fixture
    def scraper(self):
        """Create an Ontario scraper instance."""
        source = create_ontario_source()
        return OntarioScraper(source)

    def test_extract_wait_time_hours(self, scraper):
        """Extract wait time from text with hours."""
        assert scraper._extract_wait_time_hours("2.5") == 2.5
        assert scraper._extract_wait_time_hours("0.5") == 0.5
        assert scraper._extract_wait_time_hours("10.0") == 10.0
        assert scraper._extract_wait_time_hours("1") == 1.0

    def test_extract_wait_time_hours_with_text(self, scraper):
        """Extract wait time from text with surrounding context."""
        assert scraper._extract_wait_time_hours("Average: 2.5 hours") == 2.5
        assert scraper._extract_wait_time_hours("0.5 hrs") == 0.5

    def test_extract_wait_time_hours_none(self, scraper):
        """Return None for invalid text."""
        assert scraper._extract_wait_time_hours("N/A") is None
        assert scraper._extract_wait_time_hours("Unknown") is None
        assert scraper._extract_wait_time_hours("") is None

    def test_fetch_retries_with_extended_timeout_after_read_timeout(self, scraper):
        """Ontario fetch should retry once with a longer read timeout before failing."""
        mock_response = Mock()
        mock_response.text = "<html>Ontario</html>"

        captured_timeouts: list[httpx.Timeout] = []

        def side_effect(url, timeout, follow_redirects):
            captured_timeouts.append(timeout)
            assert follow_redirects is True
            if len(captured_timeouts) == 1:
                raise httpx.ReadTimeout("The read operation timed out")
            return mock_response

        with patch.object(scraper.client, "get", side_effect=side_effect):
            result = scraper.fetch()

        assert result == "<html>Ontario</html>"
        assert len(captured_timeouts) == 2
        assert captured_timeouts[0].read == 30.0
        assert captured_timeouts[1].read == 90.0

    def test_fetch_raises_after_retries_when_timeout_persists(self, scraper):
        """Ontario fetch should still fail after tenacity retries if both attempts time out."""
        with patch.object(
            scraper.client,
            "get",
            side_effect=httpx.ReadTimeout("The read operation timed out"),
        ):
            with pytest.raises(RetryError):
                scraper.fetch()

    def test_fetch_follows_current_ontario_redirect_chain(self, scraper):
        """Ontario fetch should tolerate the public source URL redirect chain."""
        final_html = "<html><table><tr><td>CHEO</td><td>0.5</td></tr></table></html>"

        def handler(request: httpx.Request) -> httpx.Response:
            request_url = str(request.url)
            if (
                request_url
                == "https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments"
            ):
                return httpx.Response(
                    301,
                    headers={
                        "Location": (
                            "https://ontariohealth.ca/system-performance/"
                            "time-spent-in-emergency-departments"
                        )
                    },
                    request=request,
                )
            if (
                request_url
                == "https://ontariohealth.ca/system-performance/time-spent-in-emergency-departments"
            ):
                return httpx.Response(
                    301,
                    headers={
                        "Location": (
                            "/system/reporting/performance/time-spent-in-emergency-departments.html"
                        )
                    },
                    request=request,
                )
            if (
                request_url == "https://ontariohealth.ca/system/reporting/performance/"
                "time-spent-in-emergency-departments.html"
            ):
                return httpx.Response(
                    301,
                    headers={
                        "Location": (
                            "https://ontariohealth.ca/system/reporting/performance/"
                            "time-spent-in-emergency-departments"
                        )
                    },
                    request=request,
                )
            if (
                request_url == "https://ontariohealth.ca/system/reporting/performance/"
                "time-spent-in-emergency-departments"
            ):
                return httpx.Response(200, text=final_html, request=request)
            return httpx.Response(404, request=request)

        scraper.client.close()
        scraper.client = httpx.Client(transport=httpx.MockTransport(handler))

        assert scraper.fetch() == final_html

    def test_normalize_hospital_id_exact_match(self, scraper):
        """Normalize hospital name to ID (exact match)."""
        assert (
            scraper._normalize_hospital_id("The Ottawa Hospital - Civic Campus")
            == "ca-on-ottawa-civic"
        )
        assert scraper._normalize_hospital_id("Toronto General Hospital") == "ca-on-toronto-general"

    def test_normalize_hospital_id_does_not_fuzzy_match(self, scraper):
        """Partial overlaps with a mapped name are skipped, not guessed."""
        assert scraper._normalize_hospital_id("SickKids Emergency") is None
        assert scraper._normalize_hospital_id("The Ottawa Hospital - Civic") is None

    def test_normalize_hospital_id_exact_match_ignores_case_and_spacing(self, scraper):
        assert scraper._normalize_hospital_id("  toronto  GENERAL hospital ") == (
            "ca-on-toronto-general"
        )
        assert scraper._normalize_hospital_id("Children\u2019s Hospital of Eastern Ontario") == (
            "ca-on-cheo"
        )

    def test_normalize_hospital_id_generates_slug(self, scraper):
        """Generate slug for unknown hospital."""
        result = scraper._normalize_hospital_id("New Ontario Hospital")
        assert result == "ca-on-new-ontario-hospital"

    def test_parse_table_format(self, scraper):
        """Parse table-based HTML format."""
        html = """
        <table>
            <tr>
                <th>Hospital Name</th>
                <th>Average (Hours)</th>
            </tr>
            <tr>
                <td>The Ottawa Hospital - Civic Campus</td>
                <td>2.5</td>
            </tr>
            <tr>
                <td>Toronto General Hospital</td>
                <td>1.5</td>
            </tr>
        </table>
        """
        measurements = scraper.parse(html)

        assert len(measurements) == 2
        assert measurements[0].hospital_id == "ca-on-ottawa-civic"
        assert measurements[0].value == 150.0  # 2.5 hours * 60 min
        assert measurements[1].hospital_id == "ca-on-toronto-general"
        assert measurements[1].value == 90.0  # 1.5 hours * 60 min

    def test_parse_with_extra_columns(self, scraper):
        """Parse table with more than 2 columns."""
        html = """
        <table>
            <tr>
                <th>Hospital</th>
                <th>Average</th>
                <th>vs Ontario Average</th>
            </tr>
            <tr>
                <td>Sunnybrook Health Sciences Centre</td>
                <td>3.0</td>
                <td>Better</td>
            </tr>
        </table>
        """
        measurements = scraper.parse(html)

        assert len(measurements) == 1
        assert measurements[0].hospital_id == "ca-on-sunnybrook"
        assert measurements[0].value == 180.0  # 3.0 hours * 60 min

    def test_measurement_has_correct_ontology(self, scraper):
        """Verify measurements are tagged with Ontario's methodology."""
        html = """
        <table>
            <tr><th>Hospital</th><th>Hours</th></tr>
            <tr><td>Mount Sinai Hospital</td><td>1.0</td></tr>
        </table>
        """
        measurements = scraper.parse(html)

        m = measurements[0]
        assert m.metric_family == MetricFamily.TIME_TO_PROVIDER
        assert m.start_event == StartEvent.TRIAGE
        assert m.end_event == EndEvent.PHYSICIAN
        assert m.statistic_type == StatisticType.MEAN  # Ontario uses MEAN not P90
        assert m.patient_scope == PatientScope.ALL
        assert m.source_id == "ontario-health"

    def test_measurement_has_payload_hash(self, scraper):
        """Verify payload is hashed for storage safety."""
        html = """
        <table>
            <tr><th>Hospital</th><th>Hours</th></tr>
            <tr><td>CHEO</td><td>0.5</td></tr>
        </table>
        """
        measurements = scraper.parse(html)

        m = measurements[0]
        assert len(m.raw_payload_hash) == 64  # SHA256
        assert m.raw_payload_snippet is not None
        assert len(m.raw_payload_snippet) <= 200

    def test_parse_empty_html(self, scraper):
        """Handle empty HTML gracefully."""
        measurements = scraper.parse("<html><body></body></html>")
        assert measurements == []

    def test_parse_no_valid_wait_times(self, scraper):
        """Handle HTML with hospitals but no valid wait times."""
        html = """
        <table>
            <tr><th>Hospital</th><th>Hours</th></tr>
            <tr><td>Hospital A</td><td>N/A</td></tr>
            <tr><td>Hospital B</td><td>Unknown</td></tr>
        </table>
        """
        measurements = scraper.parse(html)
        assert measurements == []

    def test_hours_to_minutes_conversion(self, scraper):
        """Verify hours are correctly converted to minutes."""
        html = """
        <table>
            <tr><th>Hospital</th><th>Hours</th></tr>
            <tr><td>CHEO</td><td>0.5</td></tr>
            <tr><td>Montfort Hospital</td><td>2.0</td></tr>
            <tr><td>Queensway Carleton Hospital</td><td>1.75</td></tr>
        </table>
        """
        measurements = scraper.parse(html)

        assert measurements[0].value == 30.0  # 0.5h * 60
        assert measurements[1].value == 120.0  # 2.0h * 60
        assert measurements[2].value == 105.0  # 1.75h * 60

    def test_source_factory(self):
        """Verify source factory creates correct configuration."""
        source = create_ontario_source()

        assert source.id == "ontario-health"
        assert source.name == "Health Quality Ontario"
        assert source.province == "ON"
        assert (
            source.url == "https://ontariohealth.ca/system/reporting/performance/"
            "time-spent-in-emergency-departments"
        )
        assert source.telehealth_name == "Health811"
        assert source.telehealth_number == "811"
        assert source.default_metric_family == MetricFamily.TIME_TO_PROVIDER
        assert source.default_start_event == StartEvent.TRIAGE
        assert source.default_end_event == EndEvent.PHYSICIAN
        assert source.default_statistic_type == StatisticType.MEAN

    def test_multiple_tables_parsed(self, scraper):
        """Handle pages with multiple tables."""
        html = """
        <table id="summary">
            <tr><th>Summary</th><th>Value</th></tr>
            <tr><td>Total Hospitals</td><td>100</td></tr>
        </table>
        <table id="data">
            <tr><th>Hospital</th><th>Hours</th></tr>
            <tr><td>Toronto General Hospital</td><td>2.0</td></tr>
        </table>
        """
        measurements = scraper.parse(html)

        # Should find hospital from second table, ignore first
        assert len(measurements) >= 1
        assert any(m.hospital_id == "ca-on-toronto-general" for m in measurements)

    def test_case_insensitive_hospital_matching(self, scraper):
        """Hospital name matching should be case insensitive."""
        html = """
        <table>
            <tr><th>Hospital</th><th>Hours</th></tr>
            <tr><td>THE OTTAWA HOSPITAL - CIVIC CAMPUS</td><td>1.0</td></tr>
            <tr><td>toronto general hospital</td><td>1.5</td></tr>
        </table>
        """
        measurements = scraper.parse(html)

        # Should still match despite different casing
        assert len(measurements) == 2
        hospital_ids = {m.hospital_id for m in measurements}
        assert "ca-on-ottawa-civic" in hospital_ids
        assert "ca-on-toronto-general" in hospital_ids


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "scrapers"

MULTI_SITE_IDS = {
    "ca-on-hamilton-health",
    "ca-on-william-osler",
    "ca-on-scarborough",
    "ca-on-toronto-general",
    "ca-on-kingston-health",
}


@pytest.mark.unit
class TestOntarioHospitalIdMatching:
    """Rows must never share a hospital ID or write aggregates as hospitals."""

    @pytest.fixture
    def scraper(self):
        return OntarioScraper(create_ontario_source())

    @pytest.fixture
    def fixture_html(self):
        return (FIXTURES / "ontario_ed_table.html").read_text(encoding="utf-8")

    def test_provincial_row_is_never_written_as_a_hospital(self, scraper, fixture_html):
        measurements = scraper.parse(fixture_html)

        assert ("Ontario", "aggregate row") in scraper.match_report.skipped
        assert "ca-on-ontario" not in {m.hospital_id for m in measurements}
        # CHEO carries only its own exact row (2.8 h), not the provincial 1.7 h.
        cheo = [m for m in measurements if m.hospital_id == "ca-on-cheo"]
        assert [m.value for m in cheo] == [pytest.approx(2.8 * 60)]

    @pytest.mark.parametrize(
        "name",
        ["Ontario", "ONTARIO", " Ontario Average ", "Provincial Average", "Total"],
    )
    def test_aggregate_rows_are_skipped(self, scraper, name):
        html = (
            f"<table><tr><th>H</th><th>Hours</th></tr><tr><td>{name}</td><td>1.7</td></tr></table>"
        )
        assert scraper.parse(html) == []
        assert scraper.match_report.skipped == [(name.strip(), "aggregate row")] or (
            scraper.match_report.skipped[0][1] == "aggregate row"
        )

    def test_grand_river_waterloo_site_keeps_its_hospital_id(self, scraper):
        html = (
            "<table><tr><th>H</th><th>Hours</th></tr>"
            "<tr><td>Grand River Hospital Corp-Waterloo Site</td><td>2.5</td></tr></table>"
        )
        measurements = scraper.parse(html)
        assert [m.hospital_id for m in measurements] == ["ca-on-grand-river"]

    def test_name_merely_starting_with_ontario_is_not_an_aggregate(self, scraper):
        html = (
            "<table><tr><th>H</th><th>Hours</th></tr>"
            "<tr><td>Ontario Shores Centre for Mental Health</td><td>1.7</td></tr></table>"
        )
        measurements = scraper.parse(html)
        assert [m.hospital_id for m in measurements] == [
            "ca-on-ontario-shores-centre-for-mental-health"
        ]

    def test_multi_campus_rows_do_not_write_to_corporation_ids(self, scraper, fixture_html):
        measurements = scraper.parse(fixture_html)
        written = {m.hospital_id for m in measurements}

        assert not (written & MULTI_SITE_IDS)
        skipped_names = {name for name, _ in scraper.match_report.skipped}
        assert "Hamilton Health Sciences Corp-Juravinski" in skipped_names
        assert "William Osler Health System-Civic Site" in skipped_names
        assert "Kingston Health Sciences Centre-Kingston General" in skipped_names
        assert "University Health Network-General Site" in skipped_names
        assert "Scarborough Health Network-Scar.Gen.Site" in skipped_names

    def test_exact_matches_and_unrelated_names_still_resolve(self, scraper, fixture_html):
        measurements = scraper.parse(fixture_html)
        by_id = {m.hospital_id: m.value for m in measurements}

        assert by_id["ca-on-sunnybrook"] == pytest.approx(3.1 * 60)
        assert by_id["ca-on-north-york-general"] == pytest.approx(1.2 * 60)
        # Unrelated names keep their existing generated IDs (no new behaviour).
        assert "ca-on-espanola-general-hospital" in by_id
        assert "ca-on-st-joseph-s-health-care-system-hamilton" in by_id

    def test_no_two_rows_share_a_hospital_id(self, scraper, fixture_html):
        measurements = scraper.parse(fixture_html)
        ids = [m.hospital_id for m in measurements]
        assert len(ids) == len(set(ids))
        # 21 fixture rows: 1 aggregate + 14 multi-campus skipped.
        assert len(measurements) == 21 - 1 - 14
        assert len(scraper.match_report.skipped) == 15

    def test_no_new_hospital_ids_are_introduced_for_skipped_rows(self, scraper, fixture_html):
        """Skipped campuses must not fall through to generated (auto-created) IDs."""
        scraper.parse(fixture_html)
        generated_names = {name for name, _ in scraper.match_report.generated}
        skipped_names = {name for name, _ in scraper.match_report.skipped}
        assert not (generated_names & skipped_names)
        assert not any("Health Sciences Corp" in name for name in generated_names)

    def test_two_rows_with_same_id_are_both_skipped(self, scraper):
        """Alias spellings of one hospital in the same run are ambiguous."""
        html = """
        <table><tr><th>H</th><th>Hours</th></tr>
        <tr><td>CHEO</td><td>1.0</td></tr>
        <tr><td>Children's Hospital of Eastern Ontario</td><td>2.0</td></tr>
        <tr><td>Espanola General Hospital</td><td>1.0</td></tr>
        </table>"""
        measurements = scraper.parse(html)

        assert [m.hospital_id for m in measurements] == ["ca-on-espanola-general-hospital"]
        assert scraper.match_report.skipped == [
            ("CHEO", "collision on ca-on-cheo"),
            ("Children's Hospital of Eastern Ontario", "collision on ca-on-cheo"),
        ]

    def test_two_names_with_same_generated_slug_are_both_skipped(self, scraper):
        html = """
        <table><tr><th>H</th><th>Hours</th></tr>
        <tr><td>Dryden Regional Health Centre</td><td>1.0</td></tr>
        <tr><td>Dryden  Regional Health Centre.</td><td>2.0</td></tr>
        </table>"""
        assert scraper.parse(html) == []
        assert len(scraper.match_report.skipped) == 2

    def test_generated_id_equal_to_mapped_id_is_skipped(self, scraper):
        # Slug of this name is "ca-on-ottawa-civic", which belongs to a mapped campus.
        assert scraper._normalize_hospital_id("Ottawa/Civic") is None

    def test_report_is_reset_between_parses(self, scraper, fixture_html):
        scraper.parse(fixture_html)
        scraper.parse("<table></table>")
        assert scraper.match_report.skipped == []
        assert scraper.match_report.mapped == []
