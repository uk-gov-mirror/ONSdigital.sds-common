"""Tests for the SdsCommon facade."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from sds_common.sds_common import SdsCommon
from sds_common.services.auth_header_provider import AuthHeaderProvider
from sds_common.services.secret_service import SecretService


class TestSdsCommonLaziness:
    """Verify no GCP clients are instantiated at construction time."""

    def test_instantiation_does_not_raise(self, base_config):
        client = SdsCommon(config=base_config)
        assert client is not None

    def test_config_property_returns_injected_config(self, base_config):
        client = SdsCommon(config=base_config)
        assert client.config is base_config

    def test_config_property_returns_default_config_when_none_given(self, base_config):
        client = SdsCommon()
        assert client.config.PROJECT_ID is not None

    def test_secret_manager_is_lazily_created(self, base_config):
        client = SdsCommon(config=base_config)
        with patch.object(SecretService, "_create_client", return_value=MagicMock()):
            svc = client._secrets
        assert svc is not None
        assert client._secrets is svc

    def test_iap_auth_is_lazily_created(self, base_config):
        client = SdsCommon(config=base_config)
        with patch.object(SecretService, "_create_client", return_value=MagicMock()):
            provider = client.iap_auth
        assert isinstance(provider, AuthHeaderProvider)
        assert client.iap_auth is provider

    def test_iap_auth_shares_secret_manager(self, base_config):
        client = SdsCommon(config=base_config)
        with patch.object(SecretService, "_create_client", return_value=MagicMock()):
            provider = client.iap_auth
            secret_mgr = client._secrets
        assert provider.secret_service is secret_mgr

    def test_http_service_has_no_headers(self, base_config):
        """Unauthenticated http client has no headers (for GitHub etc.)."""
        client = SdsCommon(config=base_config)
        svc = client._http
        assert svc.headers is None
        assert client._http is svc

    def test_pub_sub_service_is_lazily_created(self, base_config):
        client = SdsCommon(config=base_config)
        with patch("sds_common.sds_common.PublisherClient", return_value=MagicMock()):
            svc = client.pub_sub
        assert svc is not None
        assert svc.project_id == "test-project"

    def test_firestore_is_lazily_created(self, base_config):
        client = SdsCommon(config=base_config)
        with patch("sds_common.sds_common.firestore") as mock_fs:
            mock_fs.Client.return_value = MagicMock()
            loader = client.firestore
        assert loader is not None
        assert client.firestore is loader

    def test_firestore_client_is_lazily_created(self, base_config):
        client = SdsCommon(config=base_config)
        with patch("sds_common.sds_common.firestore") as mock_fs:
            mock_fs.Client.return_value = MagicMock()
            fc = client._firestore_client
        assert fc is not None


class TestSdsCommonAuthenticatedHttpService:
    """authenticated_http is a plain @property — fresh token every access."""

    def test_authenticated_http_service_has_headers(self, base_config):
        client = SdsCommon(config=base_config)
        mock_provider = MagicMock(spec=AuthHeaderProvider)
        mock_provider.generate.return_value = {"Authorization": "******", "Content-Type": "application/json"}
        client.__dict__["iap_auth"] = mock_provider

        svc = client._authenticated_http

        mock_provider.generate.assert_called_once()
        assert svc.headers == {"Authorization": "******", "Content-Type": "application/json"}

    def test_authenticated_http_service_generates_fresh_token_each_access(self, base_config):
        """Property — not cached — so token is re-generated on every access."""
        client = SdsCommon(config=base_config)
        mock_provider = MagicMock(spec=AuthHeaderProvider)
        mock_provider.generate.return_value = {"Authorization": "******", "Content-Type": "application/json"}
        client.__dict__["iap_auth"] = mock_provider

        client._authenticated_http
        client._authenticated_http

        assert mock_provider.generate.call_count == 2


class TestSdsCommonDependencyWiring:
    """Verify wiring of injected dependencies within the facade."""

    def test_schema_validator_uses_schema_service(self, base_config):
        client = SdsCommon(config=base_config)
        mock_req_svc = MagicMock()
        client.__dict__["schemas"] = mock_req_svc
        svc = client._schema_validator
        assert svc.sds_schema_request_service is mock_req_svc

    def test_gcs_publisher_wired_correctly(self, base_config):
        client = SdsCommon(config=base_config)
        client.__dict__["schemas"] = MagicMock()
        client.__dict__["_schema_staging_files"] = MagicMock()
        pub = client.gcs_publisher
        assert pub.schema_request_service is client.schemas
        assert pub.file_service is client._schema_staging_files

    def test_github_publisher_uses_correct_github_url(self, base_config):
        client = SdsCommon(config=base_config)
        client.__dict__["schemas"] = MagicMock()
        client.__dict__["_schema_validator"] = MagicMock()
        client.__dict__["_http"] = MagicMock()
        pub = client.github_publisher
        assert pub.github_schema_url == base_config.GITHUB_SCHEMA_URL

    def test_schema_service_uses_authenticated_http(self, base_config):
        client = SdsCommon(config=base_config)
        mock_provider = MagicMock(spec=AuthHeaderProvider)
        mock_provider.generate.return_value = {"Authorization": "******"}
        client.__dict__["iap_auth"] = mock_provider
        svc = client.schemas
        assert svc.auth_header_generator == mock_provider.generate
        assert svc.auth_header_generator() == {"Authorization": "******"}

    def test_dataset_service_uses_authenticated_http(self, base_config):
        client = SdsCommon(config=base_config)
        mock_provider = MagicMock(spec=AuthHeaderProvider)
        mock_provider.generate.return_value = {"Authorization": "******"}
        client.__dict__["iap_auth"] = mock_provider
        svc = client.datasets
        assert svc.auth_header_generator == mock_provider.generate
        assert svc.auth_header_generator() == {"Authorization": "******"}


class TestSdsCommonFileServices:
    """Cover file-service lazy properties."""

    def _client_with_mock_storage(self, base_config):
        client = SdsCommon(config=base_config)
        with patch("sds_common.sds_common.storage") as mock_storage:
            mock_storage.Client.return_value = MagicMock()
            with patch("sds_common.sds_common.BucketLoader") as mock_loader_cls:
                mock_loader = MagicMock()
                mock_loader.fetch_bucket.return_value = MagicMock()
                mock_loader_cls.return_value = mock_loader
                # touch each service to pre-populate
                _ = client._schema_staging_files
                _ = client._dataset_files
        return client

    def test_schema_staging_file_service_is_lazily_created(self, base_config):
        client = self._client_with_mock_storage(base_config)
        assert client._schema_staging_files is not None

    def test_dataset_file_service_is_lazily_created(self, base_config):
        client = self._client_with_mock_storage(base_config)
        assert client._dataset_files is not None


class TestSdsCommonConvenienceMethods:
    """generate_* convenience methods delegate to iap_auth."""

    def test_iap_auth_generate_delegates(self, base_config):
        client = SdsCommon(config=base_config)
        mock_provider = MagicMock(spec=AuthHeaderProvider)
        mock_provider.generate.return_value = {"Authorization": "******"}
        client.__dict__["iap_auth"] = mock_provider

        headers = client.iap_auth.generate()

        mock_provider.generate.assert_called_once()
        assert headers == {"Authorization": "******"}

    def test_iap_auth_generate_by_impersonation_delegates(self, base_config):
        client = SdsCommon(config=base_config)
        mock_provider = MagicMock(spec=AuthHeaderProvider)
        mock_provider.generate_by_impersonation.return_value = {"Authorization": "******"}
        client.__dict__["iap_auth"] = mock_provider

        headers = client.iap_auth.generate_by_impersonation()

        mock_provider.generate_by_impersonation.assert_called_once()
        assert headers == {"Authorization": "******"}
