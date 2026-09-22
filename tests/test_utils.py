"""Tests for utility functions."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
import requests

from sds_common.models.schema_publish_errors import FilepathError, SchemaFetchError, SchemaJSONDecodeError
from sds_common.utilities.utils import decode_json_response, fetch_raw_schema_from_github, split_filename


class TestSplitFilename:
    def test_strips_extension(self):
        assert split_filename("v1.json") == "v1"

    def test_strips_extension_with_path(self):
        assert split_filename("schemas/abc/v2.json") == "v2"

    def test_no_extension(self):
        assert split_filename("myfile") == "myfile"

    def test_raises_filepath_error_on_type_error(self):
        with pytest.raises(FilepathError) as exc_info:
            split_filename(None)
        assert isinstance(exc_info.value.__cause__, TypeError)  # original TypeError chained


class TestDecodeJsonResponse:
    def test_decodes_valid_json(self):
        response = MagicMock(spec=requests.Response)
        response.json.return_value = {"key": "value"}
        assert decode_json_response(response) == {"key": "value"}

    def test_raises_schema_json_decode_error_on_bad_json(self):
        response = MagicMock(spec=requests.Response)
        response.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        with pytest.raises(SchemaJSONDecodeError) as exc_info:
            decode_json_response(response, filepath="my_schema.json")
        assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)  # original error chained
        assert exc_info.value.filepath == "my_schema.json"  # filepath context preserved


class TestFetchRawSchemaFromGithub:
    def _make_http_service(self, status_code: int, body: dict | None = None):
        svc = MagicMock()
        response = MagicMock(spec=requests.Response)
        response.status_code = status_code
        response.json.return_value = body or {}
        svc.make_get_request.return_value = response
        return svc

    def test_returns_schema_on_200(self):
        schema_body = {"properties": {"survey_id": {"enum": ["s1"]}, "schema_version": {"const": "v1"}}}
        svc = self._make_http_service(200, schema_body)
        result = fetch_raw_schema_from_github("v1.json", svc, "https://github.com/schemas/")
        assert result == schema_body
        svc.make_get_request.assert_called_once_with("https://github.com/schemas/v1.json")

    def test_raises_schema_fetch_error_on_non_200(self):
        svc = self._make_http_service(404)
        with pytest.raises(SchemaFetchError):
            fetch_raw_schema_from_github("v1.json", svc, "https://github.com/schemas/")

    def test_raises_schema_fetch_error_on_500(self):
        svc = self._make_http_service(500)
        with pytest.raises(SchemaFetchError):
            fetch_raw_schema_from_github("missing.json", svc, "https://github.com/")
