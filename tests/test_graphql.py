from typing import Any

import pytest

import today


class FakeResp:
    def __init__(self, status: int, payload: dict[str, Any]):
        self.status_code = status
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"status {self.status_code}")


def test_graphql_returns_data(monkeypatch):
    def fake_post(url, json, headers, timeout):
        assert headers["Authorization"] == "Bearer tok"
        return FakeResp(200, {"data": {"ok": 1}})

    monkeypatch.setattr(today.requests, "post", fake_post)
    assert today.graphql("q", {}, "tok") == {"ok": 1}


def test_graphql_raises_on_graphql_errors(monkeypatch):
    monkeypatch.setattr(today, "RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(
        today.requests, "post",
        lambda url, json, headers, timeout: FakeResp(200, {"errors": [{"message": "bad"}]}),
    )
    with pytest.raises(RuntimeError, match="GraphQL errors"):
        today.graphql("q", {}, "tok")


def test_graphql_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(today, "RETRY_BACKOFF_SECONDS", 0)
    calls = {"n": 0}

    def flaky_post(url, json, headers, timeout):
        calls["n"] += 1
        if calls["n"] < 2:
            return FakeResp(503, {})
        return FakeResp(200, {"data": {"ok": True}})

    monkeypatch.setattr(today.requests, "post", flaky_post)
    assert today.graphql("q", {}, "tok") == {"ok": True}
    assert calls["n"] == 2
