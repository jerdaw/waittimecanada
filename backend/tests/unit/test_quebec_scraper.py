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
        assert scraper._normalize_hospital_id("Jewish General Hospital") == "ca-qc-jewish-general"

    def test_normalize_hospital_id_fuzzy_match(self, scraper):
        """Normalize hospital name to ID (fuzzy match)."""
        # Contains "Jewish"
        assert (
            scraper._normalize_hospital_id("Hôpital général juif de Montréal")
            == "ca-qc-jewish-general"
        )
        # Contains "Notre-Dame" - should find Hôpital Notre-Dame mapping
        assert scraper._normalize_hospital_id("Hôpital Notre-Dame") == "ca-qc-notre-dame"

    def test_normalize_hospital_id_generates_slug(self, scraper):
        """Generate slug for unknown hospital."""
        result = scraper._normalize_hospital_id("Hôpital Nouveau")
        assert result == "ca-qc-hopital-nouveau"

    def test_parse_new_format(self, scraper):
        """Parse new search-result HTML format with wait time and occupancy."""

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

        # Should now extract 3 measurements: CHUM wait time, CHUM occupancy, Jewish General wait time
        assert len(measurements) == 3

        # Check first hospital (CHUM) - wait time measurement
        assert measurements[0].hospital_id == "ca-qc-chum"
        assert measurements[0].value == 135.0  # 2h 15min
        assert measurements[0].metric_family == MetricFamily.TIME_TO_PROVIDER

        # Check first hospital (CHUM) - occupancy measurement
        assert measurements[1].hospital_id == "ca-qc-chum"
        assert measurements[1].value == 110.0  # 110%
        assert measurements[1].metric_family == MetricFamily.STRETCHER_OCCUPANCY
        assert measurements[1].statistic_type == StatisticType.POINT_ESTIMATE

        # Check second hospital (Jewish General) - wait time only
        assert measurements[2].hospital_id == "ca-qc-jewish-general"
        assert measurements[2].value == 45.0  # 45 min
        assert measurements[2].metric_family == MetricFamily.TIME_TO_PROVIDER

    def test_parse_extracts_occupancy_only(self, scraper):
        """Extract occupancy measurement when wait time is not available."""
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

        # Should extract 1 occupancy measurement (wait time not present)
        assert len(measurements) == 1
        assert measurements[0].hospital_id == "ca-qc-chum"
        assert measurements[0].value == 150.0
        assert measurements[0].metric_family == MetricFamily.STRETCHER_OCCUPANCY
        assert measurements[0].statistic_type == StatisticType.POINT_ESTIMATE

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

    def test_extract_occupancy_percentage(self, scraper):
        """Extract occupancy percentage from various text formats."""
        assert scraper._extract_occupancy_percentage("Occupancy rate: 110%") == 110.0
        assert scraper._extract_occupancy_percentage("Taux d'occupation: 127%") == 127.0
        assert scraper._extract_occupancy_percentage("150%") == 150.0
        assert scraper._extract_occupancy_percentage("95.5%") == 95.5
        assert scraper._extract_occupancy_percentage("Occupancy rate of stretchers: 85%") == 85.0

    def test_extract_occupancy_percentage_none(self, scraper):
        """Return None for text without percentage."""
        assert scraper._extract_occupancy_percentage("N/A") is None
        assert scraper._extract_occupancy_percentage("Unknown") is None
        assert scraper._extract_occupancy_percentage("") is None
        assert scraper._extract_occupancy_percentage("Number of people waiting: 10") is None

    def test_parse_french_occupancy_text(self, scraper):
        """Extract occupancy from French text."""
        html = """
        <div class="hospital_element">
            <div class="font-weight-bold">Hôpital Maisonneuve-Rosemont</div>
            <ul class="list-unstyled">
                <li class="hopital-item">
                   Taux d'occupation sur civière : 127%
                </li>
                <li class="hopital-item">
                   Temps d'attente estimé : 3 h 30 min
                </li>
            </ul>
        </div>
        """
        measurements = scraper.parse(html)

        # Should extract both wait time and occupancy
        assert len(measurements) == 2

        # Find occupancy measurement
        occupancy_measurements = [
            m for m in measurements if m.metric_family == MetricFamily.STRETCHER_OCCUPANCY
        ]
        assert len(occupancy_measurements) == 1
        assert occupancy_measurements[0].value == 127.0

    def test_parse_multiple_facilities_with_mixed_data(self, scraper):
        """Parse multiple facilities where some have occupancy and others don't."""
        html = """
        <div class="hospital_element">
            <div class="font-weight-bold">CHUM</div>
            <ul class="list-unstyled">
                <li class="hopital-item">Estimated waiting time : 90 min</li>
                <li class="hopital-item">Occupancy rate: 125%</li>
            </ul>
        </div>
        <div class="hospital_element">
            <div class="font-weight-bold">Jewish General Hospital</div>
            <ul class="list-unstyled">
                <li class="hopital-item">Estimated waiting time : 60 min</li>
            </ul>
        </div>
        """
        measurements = scraper.parse(html)

        # Should extract 3 measurements: CHUM wait+occupancy, Jewish wait only
        assert len(measurements) == 3

        # Verify we have 2 wait time measurements and 1 occupancy measurement
        wait_time_measurements = [
            m for m in measurements if m.metric_family == MetricFamily.TIME_TO_PROVIDER
        ]
        occupancy_measurements = [
            m for m in measurements if m.metric_family == MetricFamily.STRETCHER_OCCUPANCY
        ]
        assert len(wait_time_measurements) == 2
        assert len(occupancy_measurements) == 1

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
