"""Tests for SdsSchemaRequestService."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from sds_common.models.schema_publish_errors import SchemaMetadataError, SchemaPostError


@pytest.fixture
def make_response():
    def _make_response(status_code: int, body=None):
        resp = MagicMock(spec=requests.Response)
        resp.status_code = status_code
        resp.json.return_value = body if body is not None else {}
        return resp

    return _make_response


class TestGetSchemaMetadata:
    def test_returns_list_on_200(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(200, [{"schema_version": "v1"}])
        result = svc.get_metadata("surv1")
        assert result == [{"schema_version": "v1"}]

    def test_returns_none_on_404(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(404)
        assert svc.get_metadata("new_survey") is None

    def test_raises_on_500_and_logs_warning(self, mock_schema_request_service, make_response):
        from unittest.mock import patch
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(500)
        with patch("sds_common.services.sds_schema_request_service.logger") as mock_logger:
            with pytest.raises(SchemaMetadataError):
                svc.get_metadata("surv1")
        mock_logger.warning.assert_called_once()

    def test_calls_correct_url_with_survey_id(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(200, [])
        svc.get_metadata("surv1")
        http.session.get.assert_called_once_with(
            "https://sds.test/schemas/metadata", headers=None, params={"survey_id": "surv1"}
        )


class TestGetAllSchemaMetadata:
    def test_returns_list_on_200(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(200, [{"survey_id": "s1"}])
        result = svc.get_all_metadata()
        assert result == [{"survey_id": "s1"}]

    def test_raises_on_error(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(503, {})
        with pytest.raises(SchemaMetadataError):
            svc.get_all_metadata()

    def test_calls_correct_url(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.get.return_value = make_response(200, [])
        svc.get_all_metadata()
        http.session.get.assert_called_once_with("https://sds.test/schemas/all-metadata", headers=None)


VALID_SCHEMA_JSON = {
    "properties": {
        "survey_id": {"enum": ["surv1"]},
        "schema_version": {"const": "v1"},
    }
}


class TestPostSchema:
    def test_post_schema_200_returns_response(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.post.return_value = make_response(200)
        resp = svc.publish(VALID_SCHEMA_JSON, "v1.json")
        assert resp.status_code == 200

    def test_post_schema_calls_correct_url(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.post.return_value = make_response(200)
        svc.publish(VALID_SCHEMA_JSON, "v1.json")
        http.session.post.assert_called_once_with(
            "https://sds.test/schemas", json=VALID_SCHEMA_JSON, headers=None, params={"survey_id": "surv1"}
        )

    def test_post_schema_raises_on_non_200(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.post.return_value = make_response(400)
        with pytest.raises(SchemaPostError):
            svc.publish(VALID_SCHEMA_JSON, "v1.json")

    def test_post_schema_raises_survey_id_error_on_missing_field(self, mock_schema_request_service):
        from sds_common.models.schema_publish_errors import SurveyIDError
        svc, _ = mock_schema_request_service
        with pytest.raises(SurveyIDError):
            svc.publish({"properties": {}}, "bad.json")

    def test_post_schema_uses_na_filepath_by_default(self, mock_schema_request_service, make_response):
        svc, http = mock_schema_request_service
        http.session.post.return_value = make_response(200)
        svc.publish(VALID_SCHEMA_JSON)  # no filepath arg
