"""Tests for SecretService."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import GoogleAPICallError

from sds_common.models.auth_errors import SecretAccessError, SecretKeyError
from sds_common.services.secret_service import SecretService


def _make_secret_client(payload: str):
    client = MagicMock()
    response = MagicMock()
    response.payload.data = payload.encode("UTF-8")
    client.access_secret_version.return_value = response
    return client


class TestSecretService:
    def test_get_oauth_client_id_success(self, base_config):
        secret_payload = json.dumps({"web": {"client_id": "my-client-id-123"}})
        svc = SecretService(config=base_config, client=_make_secret_client(secret_payload))
        assert svc.get_oauth_client_id() == "my-client-id-123"

    def test_get_oauth_client_id_raises_secret_key_error_when_missing(self, base_config):
        secret_payload = json.dumps({"web": {}})
        svc = SecretService(config=base_config, client=_make_secret_client(secret_payload))
        with pytest.raises(SecretKeyError) as exc_info:
            svc.get_oauth_client_id()
        assert isinstance(exc_info.value.__cause__, KeyError)  # original KeyError chained

    def test_get_oauth_client_id_raises_secret_key_error_when_no_web_key(self, base_config):
        secret_payload = json.dumps({"other": "data"})
        svc = SecretService(config=base_config, client=_make_secret_client(secret_payload))
        with pytest.raises(SecretKeyError) as exc_info:
            svc.get_oauth_client_id()
        assert isinstance(exc_info.value.__cause__, KeyError)

    def test_get_secret_version_raises_secret_access_error_on_gcp_error(self, base_config):
        client = MagicMock()
        client.access_secret_version.side_effect = GoogleAPICallError("gcp error")
        svc = SecretService(config=base_config, client=client)
        with pytest.raises(SecretAccessError) as exc_info:
            svc._get_secret_version()
        assert isinstance(exc_info.value.__cause__, GoogleAPICallError)  # original GCP error chained

    def test_secret_service_reads_project_and_secret_from_config(self, base_config):
        svc = SecretService(config=base_config, client=MagicMock())
        assert svc.project_id == "test-project"
        assert svc.secret_id == "test-secret"

    def test_correct_secret_path_is_constructed(self, base_config):
        secret_payload = json.dumps({"web": {"client_id": "cid"}})
        client = _make_secret_client(secret_payload)
        svc = SecretService(config=base_config, client=client)
        svc._get_secret_version()
        client.access_secret_version.assert_called_once_with(
            name="projects/test-project/secrets/test-secret/versions/latest"
        )

    def test_secret_key_error_is_logged(self, base_config):
        from unittest.mock import patch
        secret_payload = json.dumps({"web": {}})
        svc = SecretService(config=base_config, client=_make_secret_client(secret_payload))
        with patch("sds_common.services.secret_service.logger") as mock_logger:
            with pytest.raises(SecretKeyError):
                svc.get_oauth_client_id()
        mock_logger.warning.assert_called_once()

    def test_secret_access_error_is_logged(self, base_config):
        from unittest.mock import patch
        client = MagicMock()
        client.access_secret_version.side_effect = GoogleAPICallError("gcp error")
        svc = SecretService(config=base_config, client=client)
        with patch("sds_common.services.secret_service.logger") as mock_logger:
            with pytest.raises(SecretAccessError):
                svc._get_secret_version()
        mock_logger.warning.assert_called_once()
        from sds_common.models.auth_errors import SdsAuthError
        from sds_common.models.schema_publish_errors import SchemaPublishError
        err = SecretAccessError("gcp boom")
        assert isinstance(err, SdsAuthError)
        assert not isinstance(err, SchemaPublishError)
        assert "gcp boom" in str(err)

    def test_secret_key_error_is_not_schema_publish_error(self):
        from sds_common.models.auth_errors import SdsAuthError
        from sds_common.models.schema_publish_errors import SchemaPublishError
        err = SecretKeyError()
        assert isinstance(err, SdsAuthError)
        assert not isinstance(err, SchemaPublishError)
        assert "OAuth client ID" in str(err)


class TestSecretServiceCreateClient:
    def test_create_client_uses_injected_client(self, base_config):
        mock_client_instance = MagicMock()
        svc = SecretService(config=base_config, client=mock_client_instance)
        assert svc.client is mock_client_instance

    def test_create_client_called_when_no_client_injected(self, base_config):
        mock_client_instance = MagicMock()
        with patch.object(SecretService, "_create_client", return_value=mock_client_instance):
            svc = SecretService(config=base_config)
        assert svc.client is mock_client_instance

    def test_create_client_raises_module_not_found_when_package_missing(self):
        import sys
        original = sys.modules.get("google.cloud.secretmanager")
        sys.modules["google.cloud.secretmanager"] = None  # type: ignore
        try:
            with pytest.raises((ModuleNotFoundError, ImportError)):
                SecretService._create_client()
        finally:
            if original is None:
                sys.modules.pop("google.cloud.secretmanager", None)
            else:
                sys.modules["google.cloud.secretmanager"] = original

    def test_create_client_returns_client_when_module_available(self):
        mock_instance = MagicMock()
        mock_cls = MagicMock(return_value=mock_instance)
        with patch.dict("sys.modules", {"google.cloud.secretmanager": MagicMock(SecretManagerServiceClient=mock_cls)}):
            result = SecretService._create_client()
        assert result is mock_instance
