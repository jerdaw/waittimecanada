"""Unit tests for BC scraper."""

import json

import pytest
from waittime.core import EndEvent, MetricFamily, StartEvent, StatisticType
from waittime.scrapers.bc import BCScraper, create_bc_source


@pytest.mark.unit
class TestBCScraper:
    """Tests for BC PHSA scraper."""

    @pytest.fixture
    def scraper(self):
        """Create a BC scraper instance."""
        source = create_bc_source()
        return BCScraper(source)

    @pytest.fixture
    def sample_html(self):
        """Sample HTML with __NEXT_DATA__ JSON."""
        next_data = {
            "props": {
                "pageProps": {
                    "locationsWithWaitTimes": [
                        {
                            "id": "vgh-ed",
                            "name": "Vancouver General Hospital",
                            "type": "ed",
                            "latitude": 49.2606,
                            "longitude": -123.1236,
                            "waitTime": {
                                "waitTimeMinutes": 282,
                                "elosMinutes": 601,
                                "status": "normal",
                                "createdAt": "2026-02-06T20:38:00.000Z",
                            },
                        },
                        {
                            "id": "st-pauls-ed",
                            "name": "St. Paul's Hospital",
                            "type": "ed",
                            "latitude": 49.2832,
                            "longitude": -123.1293,
                            "waitTime": {
                                "waitTimeMinutes": 95,
                                "elosMinutes": 274,
                                "status": "normal",
                                "createdAt": "2026-02-06T20:38:00.000Z",
                            },
                        },
                        {
                            "id": "ubc-upcc",
                            "name": "UBC Hospital",
                            "type": "upcc",
                            "latitude": 49.2576,
                            "longitude": -123.2424,
                            "waitTime": None,
                        },
                    ]
                }
            },
            "page": "/legacy",
        }

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BC Emergency Wait Times</title>
        </head>
        <body>
            <div id="__next"></div>
            <script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>
        </body>
        </html>
        """
        return html

    def test_generate_slug(self, scraper):
        """Test slug generation from hospital name."""
        assert scraper._generate_slug("Vancouver General Hospital") == "vancouver-general-hospital"
        assert scraper._generate_slug("St. Paul's Hospital") == "st-pauls-hospital"
        assert scraper._generate_slug("BC Children's") == "bc-childrens"
        assert (
            scraper._generate_slug("Surrey Memorial Hospital (Adult Emergency)")
            == "surrey-memorial-hospital-adult-emergency"
        )

    def test_parse_extracts_ed_locations(self, scraper, sample_html):
        """Parse should extract only ED locations, not UPCCs."""
        measurements = scraper.parse(sample_html)

        # Should get 2 EDs, not the UPCC
        assert len(measurements) == 2

    def test_parse_creates_correct_measurements(self, scraper, sample_html):
        """Parse should create measurements with correct values."""
        measurements = scraper.parse(sample_html)

        # First measurement - Vancouver General
        assert measurements[0].hospital_id == "ca-bc-vgh"
        assert measurements[0].value == 282.0
        assert measurements[0].metric_family == MetricFamily.TIME_TO_PROVIDER
        assert measurements[0].start_event == StartEvent.TRIAGE
        assert measurements[0].end_event == EndEvent.PHYSICIAN
        assert measurements[0].statistic_type == StatisticType.P90

        # Second measurement - St. Paul's
        assert measurements[1].hospital_id == "ca-bc-st-pauls"
        assert measurements[1].value == 95.0

    def test_parse_handles_unmapped_hospital(self, scraper):
        """Parse should auto-generate ID for hospitals not in mapping."""
        next_data = {
            "props": {
                "pageProps": {
                    "locationsWithWaitTimes": [
                        {
                            "id": "new-hospital",
                            "name": "New Hospital Vancouver",
                            "type": "ed",
                            "waitTime": {"waitTimeMinutes": 120},
                        }
                    ]
                }
            }
        }

        html = f"""
        <html>
        <script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>
        </html>
        """

        measurements = scraper.parse(html)

        assert len(measurements) == 1
        assert measurements[0].hospital_id == "ca-bc-new-hospital-vancouver"
        assert measurements[0].value == 120.0

    def test_parse_handles_missing_next_data(self, scraper):
        """Parse should return empty list if __NEXT_DATA__ is missing."""
        html = "<html><body>No data here</body></html>"
        measurements = scraper.parse(html)
        assert len(measurements) == 0

    def test_parse_handles_invalid_json(self, scraper):
        """Parse should handle invalid JSON gracefully."""
        html = """
        <html>
        <script id="__NEXT_DATA__" type="application/json">{ invalid json }</script>
        </html>
        """
        measurements = scraper.parse(html)
        assert len(measurements) == 0

    def test_parse_handles_unexpected_structure(self, scraper):
        """Parse should handle unexpected JSON structure."""
        next_data = {"unexpected": "structure"}

        html = f"""
        <html>
        <script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>
        </html>
        """

        measurements = scraper.parse(html)
        assert len(measurements) == 0

    def test_parse_skips_locations_without_wait_time(self, scraper):
        """Parse should skip locations with None waitTime."""
        next_data = {
            "props": {
                "pageProps": {
                    "locationsWithWaitTimes": [
                        {
                            "id": "closed-hospital",
                            "name": "Closed Hospital",
                            "type": "ed",
                            "waitTime": None,
                        },
                        {
                            "id": "open-hospital",
                            "name": "Richmond Hospital",
                            "type": "ed",
                            "waitTime": {"waitTimeMinutes": 347},
                        },
                    ]
                }
            }
        }

        html = f"""
        <html>
        <script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>
        </html>
        """

        measurements = scraper.parse(html)

        # Should only get the open hospital
        assert len(measurements) == 1
        assert measurements[0].hospital_id == "ca-bc-richmond"

    def test_parse_location_handles_missing_wait_time_minutes(self, scraper):
        """Parse should skip locations where waitTimeMinutes is None."""
        location = {
            "name": "Test Hospital",
            "type": "ed",
            "waitTime": {"waitTimeMinutes": None, "status": "closed"},
        }

        measurement = scraper._parse_location(location)
        assert measurement is None

    def test_measurement_has_correct_ontology(self, scraper, sample_html):
        """Verify measurements are tagged with BC's methodology."""
        measurements = scraper.parse(sample_html)

        for m in measurements:
            assert m.metric_family == MetricFamily.TIME_TO_PROVIDER
            assert m.start_event == StartEvent.TRIAGE
            assert m.end_event == EndEvent.PHYSICIAN
            assert m.statistic_type == StatisticType.P90
            assert m.parser_version == "v1.0"

    def test_measurement_has_payload_metadata(self, scraper, sample_html):
        """Verify measurements store payload hash and snippet."""
        measurements = scraper.parse(sample_html)

        for m in measurements:
            assert m.raw_payload_hash is not None
            assert len(m.raw_payload_hash) == 64  # SHA256 hex
            assert m.raw_payload_snippet is not None
            assert len(m.raw_payload_snippet) <= 200

    def test_create_bc_source(self):
        """Test BC source configuration."""
        source = create_bc_source()

        assert source.id == "bc-phsa"
        assert source.name == "Provincial Health Services Authority"
        assert source.province == "BC"
        assert source.url == "https://edwaittimes.ca"
        assert source.methodology_url == "https://www.edwaittimes.ca/about"
        assert source.telehealth_name == "HealthLink BC"
        assert source.telehealth_number == "811"
        assert source.default_metric_family == MetricFamily.TIME_TO_PROVIDER
        assert source.default_start_event == StartEvent.TRIAGE
        assert source.default_end_event == EndEvent.PHYSICIAN
        assert source.default_statistic_type == StatisticType.P90
