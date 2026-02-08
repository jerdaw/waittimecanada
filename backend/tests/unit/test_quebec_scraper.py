"""Unit tests for Quebec scraper."""

from unittest.mock import MagicMock, patch

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
        assert scraper._extract_wait_time("4 h 15 min") == 255.0

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

    def test_parse_new_format(self, scraper):
        """Parse new search-result HTML format."""
        
        # Simulated HTML from the AJAX endpoint
        html = """
        <div class="hospital_element">
            <div class="font-weight-bold textual-content">
                CHUM
            </div>
            <div class="adresse">1000 Rue Saint-Denis</div>
            <div class="infos-hopital">
                <ul class="list-unstyled">
                    <li class="hopital-item">
                        <span class="picto"></span>
                        Number of people waiting: <span class="font-weight-bold">15</span>
                    </li>
                    <li class="hopital-item">
                        <span class="picto"></span>
                        Estimated waiting time for non-priority cases : 
                        <span class="font-weight-bold">2 h 15 min</span>
                    </li>
                    <li class="hopital-item">
                         Occupancy rate: 110%
                    </li>
                </ul>
            </div>
        </div>
        <div class="hospital_element">
            <div class="font-weight-bold textual-content">
                Hôpital général juif
            </div>
            <div class="infos-hopital">
                <ul class="list-unstyled">
                    <li class="hopital-item">
                        Estimated waiting time for non-priority cases : 45 min
                    </li>
                </ul>
            </div>
        </div>
        """
        
        measurements = scraper.parse(html)

        assert len(measurements) == 2
        
        # Check first hospital (CHUM)
        assert measurements[0].hospital_id == "ca-qc-chum"
        assert measurements[0].value == 135.0  # 2h 15min
        
        # Check second hospital (Jewish General)
        assert measurements[1].hospital_id == "ca-qc-jewish-general"
        assert measurements[1].value == 45.0   # 45 min

    def test_parse_ignores_other_metrics(self, scraper):
        """Ensure we don't accidentally pick up occupancy rates or patient counts."""
        html = """
        <div class="hospital_element">
            <div class="font-weight-bold">CHUM</div>
            <ul class="list-unstyled">
                <li class="hopital-item">
                   Number of people waiting: 10
                </li>
                <li class="hopital-item">
                   Occupancy rate of stretchers: 150%
                </li>
            </ul>
        </div>
        """
        measurements = scraper.parse(html)
        assert len(measurements) == 0

    def test_measurement_has_correct_ontology(self, scraper):
        """Verify measurements are tagged with Quebec's methodology."""
        html = """
        <div class="hospital_element">
            <div class="font-weight-bold">CHUM</div>
            <ul class="list-unstyled">
                <li class="hopital-item">
                    Estimated waiting time for non-priority cases : 90 min
                </li>
            </ul>
        </div>
        """
        measurements = scraper.parse(html)

        assert len(measurements) == 1
        m = measurements[0]
        assert m.metric_family == MetricFamily.TIME_TO_PROVIDER
        assert m.start_event == StartEvent.REGISTRATION
        assert m.end_event == EndEvent.PHYSICIAN
        assert m.statistic_type == StatisticType.ROLLING_AVG
        assert m.source_id == "quebec-msss"

    def test_measurement_has_payload_hash(self, scraper):
        """Verify payload is hashed for storage safety."""
        html = """
        <div class="hospital_element">
            <div class="font-weight-bold">CHUM</div>
            <ul class="list-unstyled">
                <li class="hopital-item">
                    Estimated waiting time for non-priority cases : 90 min
                </li>
            </ul>
        </div>
        """
        measurements = scraper.parse(html)

        m = measurements[0]
        assert len(m.raw_payload_hash) == 64  # SHA256
        assert len(m.raw_payload_snippet) > 0

    def test_parse_empty_html(self, scraper):
        """Handle empty HTML gracefully."""
        measurements = scraper.parse("<html><body></body></html>")
        assert measurements == []

    def test_run_supports_before_save_hook(self):
        """Quebec run() should support the shared before_save persistence hook."""
        source = create_quebec_source()
        db = MagicMock()
        scraper = QuebecScraper(source, db=db)
        scraper._heartbeat = MagicMock()

        first_page_html = """
        <div class="hospital_element">
            <div class="font-weight-bold">CHUM</div>
            <ul class="list-unstyled">
                <li class="hopital-item">
                    Estimated waiting time for non-priority cases : 90 min
                </li>
            </ul>
        </div>
        """
        before_save = MagicMock()

        with (
            patch.object(scraper, "_fetch_page", side_effect=[first_page_html, "<html></html>"]),
            patch("waittime.scrapers.quebec.time.sleep", return_value=None),
        ):
            measurements = scraper.run(save_to_db=True, before_save=before_save)

        assert len(measurements) == 1
        before_save.assert_called_once_with(measurements)
        db.insert_measurements.assert_called_once_with(measurements)
        scraper._heartbeat.record_success.assert_called_once_with(
            source_id="quebec-msss",
            measurements_count=1,
        )
