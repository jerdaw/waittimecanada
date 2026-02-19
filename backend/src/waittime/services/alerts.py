"""Alert service for scraper health notifications."""

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for alert service."""

    pushover_user_key: str
    pushover_api_token: str
    enabled: bool = True


class AlertService:
    """Service for sending operational alerts via Pushover."""

    PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, config: AlertConfig | None = None):
        """
        Initialize alert service.

        Args:
            config: Optional AlertConfig. If not provided, reads from environment.
        """
        self.config = config or AlertConfig(
            pushover_user_key=os.environ.get("PUSHOVER_USER_KEY", ""),
            pushover_api_token=os.environ.get("PUSHOVER_API_TOKEN", ""),
            enabled=bool(os.environ.get("ALERTS_ENABLED", "true").lower() == "true"),
        )

    def send_alert(
        self,
        title: str,
        message: str,
        priority: int = 0,
        url: str | None = None,
    ) -> bool:
        """
        Send an alert via Pushover.

        Args:
            title: Alert title
            message: Alert body
            priority: -2 (lowest) to 2 (emergency, requires acknowledgment)
            url: Optional URL to include

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.enabled:
            logger.info("[ALERT DISABLED] %s: %s", title, message)
            return True

        if not self.config.pushover_user_key or not self.config.pushover_api_token:
            logger.warning("[ALERT NO CONFIG] %s: %s", title, message)
            return False

        payload = {
            "token": self.config.pushover_api_token,
            "user": self.config.pushover_user_key,
            "title": title,
            "message": message,
            "priority": priority,
        }
        if url:
            payload["url"] = url
            payload["url_title"] = "View Details"

        try:
            response = httpx.post(self.PUSHOVER_API_URL, data=payload, timeout=10.0)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error("[ALERT FAILED] %s", e)
            return False

    def alert_scraper_stale(self, source_id: str, age_minutes: int) -> bool:
        """
        Alert that a scraper hasn't run recently.

        Args:
            source_id: ID of the stale scraper source
            age_minutes: How long since last heartbeat

        Returns:
            True if alert sent successfully
        """
        return self.send_alert(
            title=f"⚠️ Scraper Stale: {source_id}",
            message=f"No heartbeat for {age_minutes} minutes. Check GitHub Actions.",
            priority=1,  # High priority
            url="https://github.com/jerdaw/waittimecanada/actions",
        )

    def alert_scraper_error(
        self,
        source_id: str,
        error: str,
        category: str | None = None,
        stage: str | None = None,
        run_url: str | None = None,
    ) -> bool:
        """
        Alert that a scraper encountered an error.

        Args:
            source_id: ID of the scraper that errored
            error: Error message (truncated to 200 chars)
            category: Optional failure category classification
            stage: Optional pipeline stage classification
            run_url: Optional workflow run URL for direct triage

        Returns:
            True if alert sent successfully
        """
        classification = f"{category or 'unknown'}/{stage or 'unknown'}"
        return self.send_alert(
            title=f"🚨 Scraper Error: {source_id}",
            message=f"Classification: {classification} | Error: {error[:200]}",
            priority=1,  # High priority
            url=run_url or "https://github.com/jerdaw/waittimecanada/actions",
        )
