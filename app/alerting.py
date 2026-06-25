import logging

import httpx

from app.config import settings

logger = logging.getLogger("m_motors")


def send_alert(title: str, detail: str) -> bool:
    """Sends a critical-error alert to a Slack/Discord-compatible webhook.

    Returns True if an alert was sent, False if no webhook is configured
    (no-op by design, so the app behaves identically with or without alerting
    configured) or if the webhook call itself failed.
    """
    if not settings.alert_webhook_url:
        return False

    payload = {"text": f"🚨 [M-Motors API] {title}\n{detail}", "content": f"🚨 **{title}**\n{detail}"}
    try:
        response = httpx.post(settings.alert_webhook_url, json=payload, timeout=3.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        logger.error("alert_webhook_failed", extra={"extra_fields": {"error": str(exc)}})
        return False
