from datetime import UTC, datetime
from pathlib import Path

from waittime.services.public_health_alerts import (
    HEALTH_CANADA_RECALLS_SOURCE,
    normalize_health_canada_recall_feed,
    normalize_health_canada_recall_rss,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "public_health_hub"


def test_normalize_health_canada_recall_feed() -> None:
    payload = (FIXTURES_DIR / "health_canada_recalls_sample.json").read_text(encoding="utf-8")

    alerts = normalize_health_canada_recall_feed(
        payload,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(alerts) == 2
    assert alerts[0].source_id == "health-canada-recalls"
    assert alerts[0].provenance_url == ("https://recalls-rappels.canada.ca/en/alert-recall/example")
    assert alerts[0].affected_products[0]["brand_name"] == "Example Device"
    assert alerts[1].affected_products[0]["brand_name"] == "Example Food"
    assert alerts[1].last_refreshed_at == datetime(2026, 3, 27, 12, 0, tzinfo=UTC)
    assert HEALTH_CANADA_RECALLS_SOURCE.domain == "safety_alert"


def test_normalize_health_canada_recall_rss() -> None:
    payload = """
    <rss xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
      <channel>
        <item>
          <title>Example drug recall</title>
          <link>https://recalls-rappels.canada.ca/en/alert-recall/example-drug</link>
          <description>Sample recall summary</description>
          <pubDate>2026-03-27T12:00:00</pubDate>
          <dc:creator>Drugs and health products</dc:creator>
          <guid isPermaLink="false">81802</guid>
        </item>
      </channel>
    </rss>
    """

    alerts = normalize_health_canada_recall_rss(
        payload,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(alerts) == 1
    assert alerts[0].id == "recall-81802"
    assert alerts[0].title == "Example drug recall"
    assert alerts[0].alert_type == "Drugs and health products"
    assert alerts[0].provenance_url.endswith("/example-drug")
    assert alerts[0].last_refreshed_at == datetime(2026, 3, 27, 12, 0, tzinfo=UTC)
