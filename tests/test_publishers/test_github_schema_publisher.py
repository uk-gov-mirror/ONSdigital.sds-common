"""Tests for GithubSchemaPublisher."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from sds_common.models.schema_publish_errors import SchemaDuplicationError, SchemaFetchError
from sds_common.publishers.github_schema_publisher import GithubSchemaPublisher


VALID_SCHEMA_JSON = {
    "properties": {
        "survey_id": {"enum": ["surv1"]},
        "schema_version": {"const": "v1"},
    }
}


@pytest.fixture
def http_service():
    svc = MagicMock()
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    resp.json.return_value = VALID_SCHEMA_JSON
    svc.make_get_request.return_value = resp
    return svc


@pytest.fixture
def schema_request_service():
    svc = MagicMock()
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    svc.publish.return_value = resp
    return svc


@pytest.fixture
def validator_service():
    return MagicMock()


@pytest.fixture
def publisher(schema_request_service, validator_service, http_service):
    return GithubSchemaPublisher(
        schema_request_service=schema_request_service,
        validator_service=validator_service,
        github_schema_url="https://github.com/schemas/",
        http_service=http_service,
    )


class TestGithubSchemaPublisher:
    def test_publish_schema_retrieves_validates_and_posts(self, publisher, schema_request_service, validator_service, http_service):
        publisher.publish("v1.json")
        http_service.make_get_request.assert_called_once_with("https://github.com/schemas/v1.json")
        validator_service.validate.assert_called_once()
        schema_request_service.publish.assert_called_once()

    def test_publish_schema_raises_fetch_error_on_non_200(self, publisher, http_service):
        http_service.make_get_request.return_value.status_code = 404
        with pytest.raises(SchemaFetchError):
            publisher.publish("v1.json")

    def test_publish_schema_propagates_validation_error(self, publisher, validator_service):
        validator_service.validate.side_effect = SchemaDuplicationError("v1.json")
        with pytest.raises(SchemaDuplicationError):
            publisher.publish("v1.json")

    def test_retrieve_schema_fetches_from_github_url(self, publisher, http_service):
        result = publisher._retrieve_schema("v1.json")
        assert result == VALID_SCHEMA_JSON
        http_service.make_get_request.assert_called_once_with("https://github.com/schemas/v1.json")

    def test_validate_calls_validator_service(self, publisher, validator_service):
        from sds_common.schema.schema import Schema
        schema = Schema(VALID_SCHEMA_JSON, "surv1", "v1", "v1.json")
        publisher._validate(schema)
        validator_service.validate.assert_called_once_with(schema)
