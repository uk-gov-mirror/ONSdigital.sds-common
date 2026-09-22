"""Shared pytest fixtures."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

import pytest

from tests.fakes import FakeBucketFileRepository
from sds_common.config.config import Config, get_config
from sds_common.schema.schema import Schema
from sds_common.services.file_service import FileService
from sds_common.services.pub_sub_service import PubSubService
from sds_common.services.sds_schema_request_service import SdsSchemaRequestService


@pytest.fixture(autouse=True)
def clear_config_cache():
    """Ensure the get_config lru_cache is reset between tests so env patches don't bleed across."""
    get_config.cache_clear()
    yield
    get_config.cache_clear()


@pytest.fixture
def base_config() -> Config:
    with patch.dict(
        "os.environ",
        {
            "PROJECT_ID": "test-project",
            "SDS_URL": "https://sds.test",
            "SDS_LOADER_URL": "https://loader.test",
            "HTTP_REQUEST_TIMEOUT_SECONDS": "60",
            "IAP_SECRET_ID": "test-secret",
            "FIRESTORE_DB_NAME": "test-project-sds",
            "SCHEMA_STAGING_BUCKET_NAME": "test-project-schema-publish",
            "DATASET_BUCKET_NAME": "test-project-dataset",
        },
        clear=False,
    ):
        yield Config()


@pytest.fixture
def valid_schema_json() -> dict:
    return {
        "properties": {
            "survey_id": {"enum": ["abc123"]},
            "schema_version": {"const": "v1"},
        }
    }


@pytest.fixture
def valid_schema(valid_schema_json) -> Schema:
    return Schema(valid_schema_json, "abc123", "v1", "v1.json")


@pytest.fixture
def fake_repo():
    """Empty FakeBucketFileRepository."""
    return FakeBucketFileRepository()


@pytest.fixture
def fake_repo_with_schema(valid_schema_json):
    """FakeBucketFileRepository pre-seeded with a valid schema."""
    repo = FakeBucketFileRepository()
    repo.add("v1.json", valid_schema_json)
    return repo


@pytest.fixture
def file_service(fake_repo):
    return FileService(bucket_repository=fake_repo)


@pytest.fixture
def mock_http():
    return MagicMock()


@pytest.fixture
def mock_schema_request_service(base_config):
    http = MagicMock()
    http.session = MagicMock(spec=requests.Session)
    cfg = MagicMock()
    cfg.SDS_URL = "https://sds.test"
    cfg.GET_SCHEMA_METADATA_ENDPOINT = "/schemas/metadata"
    cfg.GET_ALL_SCHEMA_METADATA_ENDPOINT = "/schemas/all-metadata"
    cfg.POST_SCHEMA_ENDPOINT = "/schemas"
    svc = SdsSchemaRequestService(http_service=http, config=cfg)
    return svc, http


@pytest.fixture
def mock_publisher_client():
    client = MagicMock()
    client.topic_path.return_value = "projects/proj/topics/my-topic"
    return client


@pytest.fixture
def pub_sub_service(mock_publisher_client):
    return PubSubService(publisher_client=mock_publisher_client, project_id="proj")


@pytest.fixture
def ok_response():
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    resp.json.return_value = {}
    return resp
