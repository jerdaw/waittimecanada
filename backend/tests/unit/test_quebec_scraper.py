"""Unit tests for Quebec scraper."""

import pytest

from waittime.core import EndEvent, MetricFamily, StartEvent, StatisticType
from waittime.scrapers.quebec import QuebecScraper, create_quebec_source


@pytest.mark.unit
class TestQuebecScraper:
    """Tests for Quebec MSSS scraper."""

    @pytest.fixture
    def scraper(self):
        """Create a Quebec scraper instance."""
        source = create_quebec_source()
        return QuebecScraper(source)

    def test_extract_wait_time_minutes(self, scraper):
        """Extract wait time from text with minutes."""
        assert scraper._extract_wait_time("120 min") == 120.0
        assert scraper._extract_wait_time("90 minutes") == 90.0
        assert scraper._extract_wait_time("45") == 45.0

    def test_extract_wait_time_hours(self, scraper):
        """Extract wait time from text with hours."""
        assert scraper._extract_wait_time("2h 30min") == 150.0
        assert scraper._extract_wait_time("3 heures") == 180.0
        assert scraper._extract_wait_time("1h 15min") == 75.0

    def test_extract_wait_time_colon_format(self, scraper):
        """Extract wait time from time format (H:MM)."""
        assert scraper._extract_wait_time("2:30") == 150.0
        assert scraper._extract_wait_time("1:45") == 105.0
        assert scraper._extract_wait_time("0:30") == 30.0

    def test_extract_wait_time_none(self, scraper):
        """Return None for invalid text."""
        assert scraper._extract_wait_time("N/A") is None
        assert scraper._extract_wait_time("Unknown") is None
        assert scraper._extract_wait_time("") is None

    def test_normalize_hospital_id_exact_match(self, scraper):
        """Normalize hospital name to ID (exact match)."""
        assert scraper._normalize_hospital_id("CHUM") == "ca-qc-chum"
        assert (
            scraper._normalize_hospital_id("Jewish General Hospital")
            == "ca-qc-jewish-general"
        )

    def test_normalize_hospital_id_fuzzy_match(self, scraper):
        """Normalize hospital name to ID (fuzzy match)."""
        # Contains "Jewish"
        assert (
            scraper._normalize_hospital_id("Hôpital général juif de Montréal")
            == "ca-qc-jewish-general"
        )
        # Contains "Notre-Dame" - should find Hôpital Notre-Dame mapping
        assert (
            scraper._normalize_hospital_id("Hôpital Notre-Dame")
            == "ca-qc-notre-dame"
        )

    def test_normalize_hospital_id_generates_slug(self, scraper):
        """Generate slug for unknown hospital."""
        result = scraper._normalize_hospital_id("Hôpital Nouveau")
        assert result == "ca-qc-hopital-nouveau"

    def test_parse_table_format(self, scraper):
        """Parse table-based HTML format."""
        html = """
        <table>
            <tr>
                <td>CHUM</td>
                <td>120 min</td>
            </tr>
            <tr>
                <td>Jewish General Hospital</td>
                <td>2h 15min</td>
            </tr>
        </table>
        """
        measurements = scraper.parse(html)

        assert len(measurements) == 2
        assert measurements[0].hospital_id == "ca-qc-chum"
        assert measurements[0].value == 120.0
        assert measurements[1].hospital_id == "ca-qc-jewish-general"
        assert measurements[1].value == 135.0

    def test_parse_json_format(self, scraper):
        """Parse embedded JSON format."""
        html = """
        <script type="application/json">
        {
            "hospitals": [
                {"name": "CHUM", "wait_time": "90"},
                {"nom": "Hôpital Maisonneuve-Rosemont", "temps_attente": "105"}
            ]
        }
        </script>
        """
        measurements = scraper.parse(html)

        assert len(measurements) == 2
        assert measurements[0].hospital_id == "ca-qc-chum"
        assert measurements[0].value == 90.0
        assert measurements[1].hospital_id == "ca-qc-maisonneuve-rosemont"
        assert measurements[1].value == 105.0

    def test_parse_card_format(self, scraper):
        """Parse card/list HTML format."""
        html = """
        <div class="hospital-card">
            <h3>CHUM</h3>
            <div class="wait-time">2:30</div>
        </div>
        <div class="hospital-card">
            <strong>Jewish General Hospital</strong>
            <span class="attente">45 min</span>
        </div>
        """
        measurements = scraper.parse(html)

        assert len(measurements) == 2
        assert measurements[0].hospital_id == "ca-qc-chum"
        assert measurements[0].value == 150.0
        assert measurements[1].hospital_id == "ca-qc-jewish-general"
        assert measurements[1].value == 45.0

    def test_measurement_has_correct_ontology(self, scraper):
        """Verify measurements are tagged with Quebec's methodology."""
        html = "<table><tr><td>CHUM</td><td>90 min</td></tr></table>"
        measurements = scraper.parse(html)

        m = measurements[0]
        assert m.metric_family == MetricFamily.TIME_TO_PROVIDER
        assert m.start_event == StartEvent.REGISTRATION
        assert m.end_event == EndEvent.PHYSICIAN
        assert m.statistic_type == StatisticType.ROLLING_AVG
        assert m.source_id == "quebec-msss"

    def test_measurement_has_payload_hash(self, scraper):
        """Verify payload is hashed for storage safety."""
        html = "<table><tr><td>CHUM</td><td>90 min</td></tr></table>"
        measurements = scraper.parse(html)

        m = measurements[0]
        assert len(m.raw_payload_hash) == 64  # SHA256
        assert m.raw_payload_snippet == html[:200]

    def test_parse_empty_html(self, scraper):
        """Handle empty HTML gracefully."""
        measurements = scraper.parse("<html><body></body></html>")
        assert measurements == []

    def test_parse_no_wait_times(self, scraper):
        """Handle HTML with hospitals but no wait times."""
        html = """
        <table>
            <tr><td>CHUM</td><td>N/A</td></tr>
            <tr><td>Jewish General</td><td>Unknown</td></tr>
        </table>
        """
        measurements = scraper.parse(html)
        assert measurements == []
