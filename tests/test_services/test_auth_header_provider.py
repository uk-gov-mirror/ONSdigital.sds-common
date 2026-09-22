"""Tests for AuthHeaderProvider."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from sds_common.services.auth_header_provider import AuthHeaderProvider
from sds_common.services.secret_service import SecretService


def _mock_secret_service(client_id: str = "test-client-id") -> SecretService:
    svc = MagicMock(spec=SecretService)
    svc.get_oauth_client_id.return_value = client_id
    return svc


def _make_provider(client_id="test-client-id", config=None, iam_client=None) -> AuthHeaderProvider:
    return AuthHeaderProvider(
        secret_service=_mock_secret_service(client_id),
        config=config,
        iam_credentials_client=iam_client,
    )


class TestAuthHeaderProviderGenerate:
    def test_generate_returns_bearer_token_headers(self, base_config):
        provider = _make_provider(config=base_config)
        with patch("google.oauth2.id_token.fetch_id_token", return_value="mytoken"):
            with patch("google.auth.transport.requests.Request"):
                headers = provider.generate()
        assert headers["Authorization"] == "Bearer mytoken"
        assert headers["Content-Type"] == "application/json"

    def test_generate_fetches_token_for_correct_audience(self, base_config):
        provider = _make_provider(client_id="the-audience", config=base_config)
        with patch("google.oauth2.id_token.fetch_id_token", return_value="tok") as mock_fetch:
            with patch("google.auth.transport.requests.Request") as mock_req_cls:
                provider.generate()
        mock_fetch.assert_called_once_with(mock_req_cls.return_value, audience="the-audience")

    def test_generate_calls_secret_service(self, base_config):
        secret_svc = _mock_secret_service("cid")
        provider = AuthHeaderProvider(secret_service=secret_svc, config=base_config)
        with patch("google.oauth2.id_token.fetch_id_token", return_value="tok"):
            with patch("google.auth.transport.requests.Request"):
                provider.generate()
        secret_svc.get_oauth_client_id.assert_called_once()


class TestAuthHeaderProviderGenerateByImpersonation:
    def test_generate_by_impersonation_returns_bearer_token_headers(self, base_config):
        iam_client = MagicMock()
        iam_client.generate_id_token.return_value = MagicMock(token="imp-token")
        provider = _make_provider(config=base_config, iam_client=iam_client)
        headers = provider.generate_by_impersonation()
        assert headers["Authorization"] == "Bearer imp-token"
        assert headers["Content-Type"] == "application/json"

    def test_generate_by_impersonation_calls_iam_with_correct_args(self, base_config):
        iam_client = MagicMock()
        iam_client.generate_id_token.return_value = MagicMock(token="tok")
        provider = _make_provider(client_id="my-client-id", config=base_config, iam_client=iam_client)
        provider.generate_by_impersonation()
        iam_client.generate_id_token.assert_called_once_with(
            name="projects/-/serviceAccounts/test-project@appspot.gserviceaccount.com",
            audience="my-client-id",
            include_email=True,
        )

    def test_generate_by_impersonation_uses_project_id_from_config(self, base_config):
        iam_client = MagicMock()
        iam_client.generate_id_token.return_value = MagicMock(token="tok")
        provider = _make_provider(config=base_config, iam_client=iam_client)
        provider.generate_by_impersonation()
        call_kwargs = iam_client.generate_id_token.call_args[1]
        assert "test-project" in call_kwargs["name"]


class TestAuthHeaderProviderCreateIamClient:
    def test_create_iam_client_returns_instance_when_module_available(self):
        mock_instance = MagicMock()
        mock_cls = MagicMock(return_value=mock_instance)
        mock_module = MagicMock()
        mock_module.IAMCredentialsClient = mock_cls
        with patch.dict(
            "sys.modules",
            {"google.cloud.iam_credentials_v1": mock_module},
        ):
            result = AuthHeaderProvider._create_iam_credentials_client()
        assert result is mock_instance

    def test_create_iam_client_raises_when_module_missing(self):
        key = "google.cloud.iam_credentials_v1"
        original = sys.modules.get(key)
        sys.modules[key] = None  # type: ignore
        try:
            with pytest.raises((ModuleNotFoundError, ImportError)):
                AuthHeaderProvider._create_iam_credentials_client()
        finally:
            if original is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = original

    def test_iam_client_lazily_created_when_not_injected(self, base_config):
        """If no iam_credentials_client is injected, it is created on first call."""
        mock_instance = MagicMock()
        mock_instance.generate_id_token.return_value = MagicMock(token="tok")
        provider = _make_provider(config=base_config)
        with patch.object(AuthHeaderProvider, "_create_iam_credentials_client", return_value=mock_instance):
            provider.generate_by_impersonation()
        mock_instance.generate_id_token.assert_called_once()
