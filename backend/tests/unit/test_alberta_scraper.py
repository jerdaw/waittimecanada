"""Unit tests for Alberta scraper."""

import pytest
from waittime.core import EndEvent, MetricFamily, PatientScope, StartEvent, StatisticType
from waittime.scrapers.alberta import AlbertaScraper, create_alberta_source


@pytest.mark.unit
class TestAlbertaScraper:
    """Tests for Alberta Health Services scraper."""

    @pytest.fixture
    def scraper(self):
        """Create an Alberta scraper instance."""
        source = create_alberta_source()
        return AlbertaScraper(source)

    @pytest.fixture
    def sample_html(self):
        """Sample HTML matching AHS wait-time card structure."""
        return """
        <html>
          <body>
            <div class="well wt-well">
              <div class="wt-times ">
                <span><strong>4</strong> <label class="hrminlabel">hr</label>
                <strong>23</strong> <label class="hrminlabel">min</label></span>
              </div>
              <div class="wt-description langDirection">
                <p class="hospitalName"><strong><a href="#">Foothills Medical Centre</a></strong></p>
                <p class="hospitalCateg"><span class="wt-category">Emergency</span></p>
              </div>
            </div>

            <div class="well wt-well">
              <div class="wt-times ">
                <span><strong>1</strong> <label class="hrminlabel">hr</label>
                <strong>8</strong> <label class="hrminlabel">min</label></span>
              </div>
              <div class="wt-description langDirection">
                <p class="hospitalName"><strong><a href="#">Airdrie Community Health Centre</a></strong></p>
                <p class="hospitalCateg"><span class="wt-category">Urgent Care</span></p>
              </div>
            </div>

            <div class="well wt-well">
              <div class="wt-times ">
                <span><label class="hrminlabel">Wait</label>
                <label class="hrminlabel">times</label>
                <label class="hrminlabel">unavailable</label></span>
              </div>
              <div class="wt-description langDirection">
                <p class="hospitalName"><strong><a href="#">Innisfail Health Centre</a></strong></p>
                <p class="hospitalCateg"><span class="wt-category">Emergency</span></p>
              </div>
            </div>

            <div class="well wt-well" id="two-wait-times">
              <div class="dbl-wt">
                <div class="wt1">
                  <span><strong>4</strong> <label class="hrminlabel">hr</label>
                  <strong>24</strong> <label class="hrminlabel">min</label>
                  <p>Adult emergency</p></span>
                </div>
                <div class="wt2">
                  <span><strong>4</strong> <label class="hrminlabel">hr</label>
                  <strong>11</strong> <label class="hrminlabel">min</label>
                  <p>Children's emergency</p></span>
                </div>
              </div>
              <div class="wt-description langDirection">
                <p class="hospitalName"><strong><a href="#">South Health Campus</a></strong></p>
                <p class="hospitalCateg"><span class="wt-category">Emergency</span></p>
              </div>
            </div>
          </body>
        </html>
        """

    def test_parse_extracts_emergency_measurements(self, scraper, sample_html):
        """Parse should include emergency cards and skip urgent care cards."""
        measurements = scraper.parse(sample_html)

        assert len(measurements) == 2
        assert {m.hospital_id for m in measurements} == {
            "ca-ab-foothills-medical-centre",
            "ca-ab-south-health-campus",
        }

    def test_parse_extracts_wait_minutes_correctly(self, scraper, sample_html):
        """Parse should convert wait text to minutes."""
        measurements = scraper.parse(sample_html)
        by_id = {m.hospital_id: m for m in measurements}

        assert by_id["ca-ab-foothills-medical-centre"].value == 263.0
        assert by_id["ca-ab-south-health-campus"].value == 264.0

    def test_parse_applies_correct_ontology(self, scraper, sample_html):
        """Measurements should be tagged with Alberta ontology."""
        measurements = scraper.parse(sample_html)

        for measurement in measurements:
            assert measurement.metric_family == MetricFamily.TIME_TO_PROVIDER
            assert measurement.start_event == StartEvent.TRIAGE
            assert measurement.end_event == EndEvent.PHYSICIAN
            assert measurement.statistic_type == StatisticType.POINT_ESTIMATE
            assert measurement.patient_scope == PatientScope.ALL
            assert measurement.parser_version == "v1.0"

    def test_measurement_payload_metadata(self, scraper, sample_html):
        """Measurements should include payload hash and snippet."""
        measurements = scraper.parse(sample_html)
        for measurement in measurements:
            assert len(measurement.raw_payload_hash) == 64
            assert measurement.raw_payload_snippet is not None
            assert len(measurement.raw_payload_snippet) <= 200

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("4 hr 23 min", 263),
            ("51 min", 51),
            ("1 hour 30 minutes", 90),
            ("Wait times unavailable", None),
            ("Closed", None),
        ],
    )
    def test_extract_wait_minutes(self, scraper, text, expected):
        """Wait-time helper should parse supported formats."""
        assert scraper._extract_wait_minutes(text) == expected

    def test_create_alberta_source(self):
        """Source factory should return Alberta source metadata."""
        source = create_alberta_source()

        assert source.id == "alberta-ahs"
        assert source.name == "Alberta Health Services"
        assert source.province == "AB"
        assert source.url == "https://www.albertahealthservices.ca/waittimes/Page14230.aspx"
        assert (
            source.methodology_url
            == "https://www.albertahealthservices.ca/waittimes/Page14230.aspx"
        )
        assert source.telehealth_name == "Health Link 811"
        assert source.telehealth_number == "811"
        assert source.default_metric_family == MetricFamily.TIME_TO_PROVIDER
        assert source.default_start_event == StartEvent.TRIAGE
        assert source.default_end_event == EndEvent.PHYSICIAN
        assert source.default_statistic_type == StatisticType.POINT_ESTIMATE
