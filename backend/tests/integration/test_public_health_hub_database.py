from datetime import UTC, date, datetime
from pathlib import Path

import psycopg2.extras
import pytest

from waittime.core import PublicDataSource
from waittime.services.database import DatabaseService

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "migrations" / "018_create_public_health_hub_tables.sql"
)


def _apply_public_health_hub_migration(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(MIGRATION_PATH.read_text(encoding="utf-8"))


def _build_source(**overrides) -> PublicDataSource:
    base = {
        "source_id": "test-mohserlo",
        "domain": "provider_facility",
        "source_name": "MOHSERLO",
        "scope": "ontario",
        "jurisdiction_level": "provincial",
        "connector_type": "open_data_portal",
        "access_route": "Ontario Data Catalogue CSV download",
        "license_reuse_status": "approved_with_conditions",
        "attribution_requirement": "OGL Ontario attribution required",
        "update_cadence": "monthly",
        "freshness_sensitivity": "low",
        "operational_risk": "low",
        "recommended_usage_mode": "scheduled_ingest",
        "provenance_url": "https://data.ontario.ca/example",
        "last_verified_at": date(2026, 3, 27),
        "notes": None,
        "fallback_source_id": None,
        "public_methodology_note": "Reference directory data only.",
        "last_refreshed_at": datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    }
    base.update(overrides)
    return PublicDataSource(**base)


@pytest.fixture
def public_health_hub_db(database_url: str):
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    try:
        _apply_public_health_hub_migration(conn)
        yield DatabaseService(conn=conn)
    finally:
        conn.rollback()
        conn.close()


class TestPublicHealthHubDatabase:
    def test_public_data_source_crud(self, public_health_hub_db: DatabaseService):
        inserted = public_health_hub_db.upsert_public_data_source(_build_source())

        assert inserted.source_id == "test-mohserlo"

        fetched = public_health_hub_db.get_public_data_source("test-mohserlo")
        assert fetched is not None
        assert fetched.source_name == "MOHSERLO"

        refreshed_at = datetime(2026, 3, 28, 10, 0, tzinfo=UTC)
        refreshed = public_health_hub_db.mark_public_data_source_refreshed(
            "test-mohserlo", refreshed_at=refreshed_at
        )
        assert refreshed.last_refreshed_at == refreshed_at

    def test_upsert_public_data_source_preserves_existing_refresh_when_new_value_is_null(
        self, public_health_hub_db: DatabaseService
    ):
        original_refreshed_at = datetime(2026, 3, 27, 12, 0, tzinfo=UTC)
        public_health_hub_db.upsert_public_data_source(
            _build_source(last_refreshed_at=original_refreshed_at)
        )

        updated = public_health_hub_db.upsert_public_data_source(
            _build_source(
                source_name="Updated MOHSERLO",
                last_refreshed_at=None,
            )
        )

        assert updated.source_name == "Updated MOHSERLO"
        assert updated.last_refreshed_at == original_refreshed_at

    def test_public_health_hub_tables_accept_resource_and_alert_rows(
        self,
        public_health_hub_db: DatabaseService,
    ):
        public_health_hub_db.upsert_public_data_source(_build_source())
        public_health_hub_db.upsert_public_data_source(
            _build_source(
                source_id="test-recalls",
                domain="safety_alert",
                source_name="Health Canada Recalls",
                scope="canada",
                jurisdiction_level="federal",
                connector_type="feed",
                access_route="Health Canada recalls CSV and RSS feeds",
                update_cadence="hourly",
                freshness_sensitivity="high",
                operational_risk="medium",
                recommended_usage_mode="scheduled_ingest",
                provenance_url="https://recalls-rappels.canada.ca/en",
                public_methodology_note="Official recall feed.",
            )
        )

        with public_health_hub_db.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO resource_locations (
                        id,
                        source_id,
                        kind,
                        source_record_id,
                        name,
                        province,
                        city,
                        latitude,
                        longitude,
                        address,
                        reference_status,
                        provenance_url,
                        last_refreshed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        "test-facility-toronto-general",
                        "test-mohserlo",
                        "facility",
                        "mohserlo-123",
                        "Toronto General Hospital",
                        "ON",
                        "Toronto",
                        43.6532,
                        -79.3832,
                        "200 Elizabeth St",
                        "directory_only",
                        "https://data.ontario.ca/example/facilities",
                        datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
                    ),
                )
                resource_row = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO public_health_alerts (
                        id,
                        source_id,
                        title,
                        summary,
                        alert_type,
                        published_at,
                        source_updated_at,
                        affected_products,
                        provenance_url,
                        last_refreshed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        "test-alert-001",
                        "test-recalls",
                        "Example recall",
                        "Sample summary",
                        "food",
                        datetime(2026, 3, 27, 9, 0, tzinfo=UTC),
                        datetime(2026, 3, 27, 9, 30, tzinfo=UTC),
                        '[{"brand_name":"Example Product","din":"12345678"}]',
                        "https://recalls-rappels.canada.ca/example-alert",
                        datetime(2026, 3, 27, 10, 0, tzinfo=UTC),
                    ),
                )
                alert_row = cur.fetchone()

        assert resource_row["kind"] == "facility"
        assert resource_row["reference_status"] == "directory_only"
        assert alert_row["alert_type"] == "food"
        assert alert_row["affected_products"][0]["brand_name"] == "Example Product"

        alerts = public_health_hub_db.list_public_health_alerts(source_id="test-recalls")
        assert len(alerts) == 1
        assert alerts[0].title == "Example recall"

        statuses = public_health_hub_db.list_public_health_source_statuses()
        assert len(statuses) == 2

        source_status = {status.source_id: status for status in statuses}
        assert source_status["test-mohserlo"].resource_record_count == 1
        assert source_status["test-mohserlo"].alert_record_count == 0
        assert source_status["test-recalls"].resource_record_count == 0
        assert source_status["test-recalls"].alert_record_count == 1
        assert source_status["test-recalls"].latest_alert_published_at == datetime(
            2026, 3, 27, 9, 0, tzinfo=UTC
        )
