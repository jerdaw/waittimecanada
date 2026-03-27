from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest

from waittime.core import PublicDataSource
from waittime.services.database import DatabaseService


@pytest.fixture
def mock_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost/db")
    return "postgresql://user@localhost/db"


@pytest.fixture
def db_service(mock_db_url):
    return DatabaseService(mock_db_url)


def make_public_data_source(**overrides) -> PublicDataSource:
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


def make_public_data_source_row(**overrides):
    row = make_public_data_source(**overrides).model_dump()
    row["created_at"] = datetime(2026, 3, 27, 12, 0, tzinfo=UTC)
    row["updated_at"] = datetime(2026, 3, 27, 12, 5, tzinfo=UTC)
    return row


class TestPublicHealthSourceCatalogDatabaseService:
    @patch("psycopg2.connect")
    def test_upsert_public_data_source(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = make_public_data_source_row()

        source = make_public_data_source()

        result = db_service.upsert_public_data_source(source)

        assert result.source_id == source.source_id
        assert result.recommended_usage_mode == "scheduled_ingest"
        mock_cursor.execute.assert_called_once()
        assert "INSERT INTO public_data_sources" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_list_public_data_sources(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            make_public_data_source_row(),
            make_public_data_source_row(
                source_id="test-aqhi",
                domain="environmental_overlay",
                source_name="AQHI GeoMet",
                scope="canada",
                jurisdiction_level="federal",
                connector_type="api",
                access_route="GeoMet API",
                update_cadence="hourly",
                freshness_sensitivity="high",
                recommended_usage_mode="live_ui",
                provenance_url="https://api.weather.gc.ca/example",
            ),
        ]

        results = db_service.list_public_data_sources()

        assert len(results) == 2
        assert results[0].source_id == "test-mohserlo"
        assert results[1].source_id == "test-aqhi"

    @patch("psycopg2.connect")
    def test_mark_public_data_source_refreshed(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        refreshed_at = datetime(2026, 3, 28, 8, 0, tzinfo=UTC)
        mock_cursor.fetchone.return_value = make_public_data_source_row(
            last_refreshed_at=refreshed_at
        )

        result = db_service.mark_public_data_source_refreshed(
            "test-mohserlo", refreshed_at=refreshed_at
        )

        assert result.last_refreshed_at == refreshed_at
        assert "UPDATE public_data_sources" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_upsert_public_data_source_preserves_existing_refresh_when_null(
        self, mock_connect, db_service
    ):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = make_public_data_source_row(
            last_refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC)
        )

        source = make_public_data_source(last_refreshed_at=None)

        db_service.upsert_public_data_source(source)

        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "COALESCE(" in executed_sql
        assert "public_data_sources.last_refreshed_at" in executed_sql
