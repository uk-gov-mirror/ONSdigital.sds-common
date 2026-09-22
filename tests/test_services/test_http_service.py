"""Tests for HttpService — pure HTTP client."""
from __future__ import annotations

from unittest.mock import MagicMock

import requests

from sds_common.services.http_service import HttpService


def _make_service(headers=None) -> HttpService:
    session = MagicMock(spec=requests.Session)
    return HttpService(session=session, headers=headers)


class TestHttpServiceSetup:
    def test_build_session_returns_requests_session(self):
        session = HttpService._build_session()
        assert isinstance(session, requests.Session)

    def test_no_headers_by_default(self):
        svc = _make_service()
        assert svc.headers is None

    def test_headers_stored_when_provided(self):
        headers = {"Authorization": "Bearer tok", "Content-Type": "application/json"}
        svc = _make_service(headers=headers)
        assert svc.headers == headers

    def test_create_factory_builds_instance_with_session(self):
        svc = HttpService.create()
        assert isinstance(svc, HttpService)
        assert isinstance(svc.session, requests.Session)
        assert svc.headers is None

    def test_create_factory_with_headers(self):
        headers = {"Authorization": "Bearer tok"}
        svc = HttpService.create(headers=headers)
        assert svc.headers == headers


class TestHttpServiceRequests:
    def test_make_get_request(self):
        session = MagicMock(spec=requests.Session)
        session.get.return_value = MagicMock(spec=requests.Response)
        svc = HttpService(session=session, headers={"Authorization": "Bearer tok"})
        result = svc.make_get_request("https://example.com", params={"k": "v"})
        session.get.assert_called_once_with(
            "https://example.com",
            headers={"Authorization": "Bearer tok"},
            params={"k": "v"},
        )
        assert result is session.get.return_value

    def test_make_get_request_no_params(self):
        session = MagicMock(spec=requests.Session)
        session.get.return_value = MagicMock()
        svc = HttpService(session=session)
        svc.make_get_request("https://example.com")
        session.get.assert_called_once_with("https://example.com", headers=None, params=None)

    def test_make_post_request(self):
        session = MagicMock(spec=requests.Session)
        session.post.return_value = MagicMock(spec=requests.Response)
        svc = HttpService(session=session, headers={"Authorization": "Bearer tok"})
        result = svc.make_post_request("https://example.com", {"data": 1}, params={"p": "q"})
        session.post.assert_called_once_with(
            "https://example.com",
            json={"data": 1},
            headers={"Authorization": "Bearer tok"},
            params={"p": "q"},
        )
        assert result is session.post.return_value

    def test_unauthenticated_get_sends_no_headers(self):
        session = MagicMock(spec=requests.Session)
        session.get.return_value = MagicMock()
        svc = HttpService(session=session)
        svc.make_get_request("https://github.com/schema.json")
        _, kwargs = session.get.call_args
        assert kwargs["headers"] is None
