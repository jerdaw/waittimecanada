from unittest.mock import MagicMock, patch

import httpx
import pytest

from waittime.services.alerts import AlertConfig, AlertService


@pytest.fixture
def mock_httpx_post():
    with patch("httpx.post") as mock_post:
        yield mock_post


class TestAlertService:
    def test_init_defaults(self, monkeypatch):
        monkeypatch.setenv("PUSHOVER_USER_KEY", "u_key")
        monkeypatch.setenv("PUSHOVER_API_TOKEN", "api_token")
        monkeypatch.setenv("ALERTS_REFERENCE_URL", "https://example.com/ops")

        service = AlertService()
        assert service.config.pushover_user_key == "u_key"
        assert service.config.pushover_api_token == "api_token"
        assert service.config.enabled is True
        assert service.config.reference_url == "https://example.com/ops"

    def test_send_alert_disabled(self):
        config = AlertConfig(pushover_user_key="k", pushover_api_token="t", enabled=False)
        service = AlertService(config)

        with patch("httpx.post") as mock_post:
            result = service.send_alert("Title", "Msg")
            assert result is True  # Returns True when disabled (no-op)
            mock_post.assert_not_called()

    def test_send_alert_missing_config(self):
        config = AlertConfig(pushover_user_key="", pushover_api_token="", enabled=True)
        service = AlertService(config)

        with patch("httpx.post") as mock_post:
            result = service.send_alert("Title", "Msg")
            assert result is False
            mock_post.assert_not_called()

    def test_send_alert_success(self, mock_httpx_post):
        config = AlertConfig(pushover_user_key="k", pushover_api_token="t", enabled=True)
        service = AlertService(config)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_httpx_post.return_value = mock_response

        result = service.send_alert("Title", "Msg", priority=1, url="http://test.com")

        assert result is True
        mock_httpx_post.assert_called_once()
        args, kwargs = mock_httpx_post.call_args
        assert kwargs["data"]["title"] == "Title"
        assert kwargs["data"]["url"] == "http://test.com"

    def test_send_alert_api_error(self, mock_httpx_post):
        config = AlertConfig(pushover_user_key="k", pushover_api_token="t", enabled=True)
        service = AlertService(config)

        mock_httpx_post.side_effect = httpx.HTTPError("API Down")

        result = service.send_alert("Title", "Msg")
        assert result is False

    def test_alert_scraper_stale(self):
        service = AlertService(AlertConfig("k", "t", reference_url="https://example.com/alerts"))
        with patch.object(service, "send_alert", return_value=True) as mock_send:
            result = service.alert_scraper_stale("source_1", 120)
            assert result is True
            mock_send.assert_called_once()
            assert "Scraper Stale: source_1" in mock_send.call_args[1]["title"]
            assert "120 minutes" in mock_send.call_args[1]["message"]
            assert mock_send.call_args[1]["url"] == "https://example.com/alerts"

    def test_alert_scraper_error_truncation(self):
        service = AlertService(AlertConfig("k", "t", reference_url="https://example.com/alerts"))
        long_error = "x" * 300
        with patch.object(service, "send_alert", return_value=True) as mock_send:
            service.alert_scraper_error("source_1", long_error)
            message = mock_send.call_args[1]["message"]
            assert len(message) < 250  # Should be truncated
            assert "unknown/unknown" in message
            assert "Error:" in message
            assert mock_send.call_args[1]["url"] == "https://example.com/alerts"

    def test_alert_scraper_resolved(self):
        service = AlertService(AlertConfig("k", "t", reference_url="https://example.com/alerts"))
        with patch.object(service, "send_alert", return_value=True) as mock_send:
            result = service.alert_scraper_resolved("source_1", "stale", duration="2h 5m")
            assert result is True
            mock_send.assert_called_once()
            assert "Scraper Recovered: source_1" in mock_send.call_args[1]["title"]
            assert "Recovered from stale incident" in mock_send.call_args[1]["message"]
            assert "2h 5m" in mock_send.call_args[1]["message"]
            assert mock_send.call_args[1]["url"] == "https://example.com/alerts"
