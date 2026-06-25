import httpx

from app import alerting


def test_send_alert_is_noop_without_webhook_configured(monkeypatch):
    monkeypatch.setattr(alerting.settings, "alert_webhook_url", None)
    assert alerting.send_alert("Test", "detail") is False


def test_send_alert_posts_to_webhook_when_configured(monkeypatch):
    monkeypatch.setattr(alerting.settings, "alert_webhook_url", "https://hooks.example.com/alert")

    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(alerting.httpx, "post", fake_post)

    assert alerting.send_alert("Crash", "boom") is True
    assert captured["url"] == "https://hooks.example.com/alert"
    assert "Crash" in captured["json"]["text"]


def test_send_alert_returns_false_when_webhook_call_fails(monkeypatch):
    monkeypatch.setattr(alerting.settings, "alert_webhook_url", "https://hooks.example.com/alert")

    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(alerting.httpx, "post", fake_post)

    assert alerting.send_alert("Crash", "boom") is False
