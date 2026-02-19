"""Unit tests for Ontario scraper."""

import pytest
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

    def test_normalize_hospital_id_exact_match(self, scraper):
        """Normalize hospital name to ID (exact match)."""
        assert (
            scraper._normalize_hospital_id("The Ottawa Hospital - Civic Campus")
            == "ca-on-ottawa-civic"
        )
        assert scraper._normalize_hospital_id("Toronto General Hospital") == "ca-on-toronto-general"

    def test_normalize_hospital_id_fuzzy_match(self, scraper):
        """Normalize hospital name to ID (fuzzy match)."""
        # Contains "SickKids"
        assert scraper._normalize_hospital_id("SickKids Emergency") == "ca-on-sickkids"

        # Contains "The Ottawa Hospital"
        assert scraper._normalize_hospital_id("The Ottawa Hospital - Civic") == "ca-on-ottawa-civic"

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
