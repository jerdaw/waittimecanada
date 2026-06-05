"""Alert service for scraper health notifications."""

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for alert service."""

    alert_user_key: str = ""
    alert_api_token: str = ""
    alert_api_url: str = ""
    enabled: bool = True
    reference_url: str = "https://github.com/jerdaw/waittimecanada/actions"


class AlertService:
    """Service for sending operational alerts through a configured provider."""

    def __init__(self, config: AlertConfig | None = None):
        """
        Initialize alert service.

        Args:
            config: Optional AlertConfig. If not provided, reads from environment.
        """
        self.config = config or AlertConfig(
            alert_user_key=os.environ.get("ALERT_USER_KEY", ""),
            alert_api_token=os.environ.get("ALERT_API_TOKEN", ""),
            alert_api_url=os.environ.get("ALERT_API_URL", ""),
            enabled=bool(os.environ.get("ALERTS_ENABLED", "true").lower() == "true"),
            reference_url=os.environ.get(
                "ALERTS_REFERENCE_URL",
                "https://github.com/jerdaw/waittimecanada/actions",
            ),
        )

    def send_alert(
        self,
        title: str,
        message: str,
        priority: int = 0,
        url: str | None = None,
    ) -> bool:
        """
        Send an alert through the configured alert provider.

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

        if (
            not self.config.alert_user_key
            or not self.config.alert_api_token
            or not self.config.alert_api_url
        ):
            logger.warning("[ALERT NO CONFIG] %s: %s", title, message)
            return False

        payload = {
            "token": self.config.alert_api_token,
            "user": self.config.alert_user_key,
            "title": title,
            "message": message,
            "priority": priority,
        }
        if url:
            payload["url"] = url
            payload["url_title"] = "View Details"

        try:
            response = httpx.post(self.config.alert_api_url, data=payload, timeout=10.0)
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
            message=f"No heartbeat for {age_minutes} minutes. Check the Wait Time Canada scraper runtime.",
            priority=1,  # High priority
            url=self.config.reference_url,
        )

    def alert_scraper_resolved(
        self,
        source_id: str,
        incident_kind: str,
        duration: str | None = None,
        run_url: str | None = None,
    ) -> bool:
        """Alert that a scraper incident has recovered."""
        message = f"Recovered from {incident_kind} incident."
        if duration:
            message = f"{message} Duration: {duration}."
        message = f"{message} Scraper heartbeat is healthy again."
        return self.send_alert(
            title=f"✅ Scraper Recovered: {source_id}",
            message=message,
            priority=0,
            url=run_url or self.config.reference_url,
        )

    def alert_public_health_source_degraded(
        self,
        source_id: str,
        *,
        source_name: str,
        reasons: list[str],
        run_url: str | None = None,
    ) -> bool:
        """Alert that a hard-fail public-health source is degraded."""
        reason_text = "; ".join(reasons)[:250]
        return self.send_alert(
            title=f"⚠️ Public Health Source Degraded: {source_name}",
            message=f"Source {source_id} is degraded. Reasons: {reason_text}",
            priority=1,
            url=run_url or self.config.reference_url,
        )

    def alert_public_health_source_resolved(
        self,
        source_id: str,
        *,
        source_name: str,
        duration: str | None = None,
        run_url: str | None = None,
    ) -> bool:
        """Alert that a public-health ingest incident has recovered."""
        message = f"{source_name} ({source_id}) is healthy again."
        if duration:
            message = f"Recovered after {duration}. {message}"
        return self.send_alert(
            title=f"✅ Public Health Source Recovered: {source_name}",
            message=message,
            priority=0,
            url=run_url or self.config.reference_url,
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
            url=run_url or self.config.reference_url,
        )
