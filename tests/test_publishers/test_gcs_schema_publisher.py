"""Tests for GcsSchemaPublisher."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from sds_common.publishers.gcs_schema_publisher import GcsSchemaPublisher
from sds_common.services.file_service import FileService
from tests.fakes import FakeBucketFileRepository


VALID_SCHEMA_JSON = {
    "properties": {
        "survey_id": {"enum": ["surv1"]},
        "schema_version": {"const": "v1"},
    }
}


@pytest.fixture
def repo():
    repo = FakeBucketFileRepository()
    repo.add("v1.json", VALID_SCHEMA_JSON)
    return repo


@pytest.fixture
def schema_request_service():
    svc = MagicMock()
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    svc.publish.return_value = resp
    return svc


@pytest.fixture
def publisher(schema_request_service, repo):
    return GcsSchemaPublisher(
        schema_request_service=schema_request_service,
        file_service=FileService(bucket_repository=repo),
    )


class TestGcsSchemaPublisher:
    def test_publish_retrieves_and_posts(self, publisher, schema_request_service):
        publisher.publish("v1.json")
        schema_request_service.publish.assert_called_once()

    def test_publish_returns_response(self, publisher):
        resp = publisher.publish("v1.json")
        assert resp.status_code == 200

    def test_publish_deletes_staged_file_on_success(self, publisher, repo):
        publisher.publish("v1.json")
        assert not repo.check_file_exists("v1.json")

    def test_publish_does_not_delete_on_failure(self, publisher, schema_request_service, repo):
        schema_request_service.publish.side_effect = RuntimeError("SDS error")
        with pytest.raises(RuntimeError):
            publisher.publish("v1.json")
        assert repo.check_file_exists("v1.json")

    def test_retrieve_schema_returns_content(self, publisher):
        result = publisher._retrieve_schema("v1.json")
        assert result == VALID_SCHEMA_JSON
