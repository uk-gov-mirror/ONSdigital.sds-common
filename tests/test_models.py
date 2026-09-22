"""Tests for data models and error classes."""
from __future__ import annotations

import json

import pytest

from sds_common.models.dataset_models import DatasetMetadata
from sds_common.models.dataset_publish_errors import DatasetCreateError, DatasetMetadataRetrievalError
from sds_common.models.auth_errors import SdsAuthError, SecretAccessError, SecretKeyError
from sds_common.models.schema_publish_errors import (
    FilepathError,
    SchemaFetchError,
    SchemaJSONDecodeError,
    SchemaMetadataError,
    SchemaMetadataFormatError,
    SchemaPostError,
    SchemaPublishError,
    SchemaDuplicationError,
    SchemaVersionError,
    SchemaVersionMismatchError,
    SurveyIDError,
)


class TestDatasetMetadata:
    def test_construction(self):
        dm = DatasetMetadata(
            dataset_id="d1",
            survey_id="s1",
            period_id="p1",
            form_types=["f1"],
            sds_published_at="2024-01-01",
            total_reporting_units=10,
            sds_dataset_version=1,
            filename="file.json",
        )
        assert dm.dataset_id == "d1"
        assert dm.title is None

    def test_title_optional(self):
        dm = DatasetMetadata(
            dataset_id="d1", survey_id="s1", period_id="p1",
            form_types=[], sds_published_at="", total_reporting_units=0,
            sds_dataset_version=0, filename="", title="My Title",
        )
        assert dm.title == "My Title"


class TestDatasetPublishErrors:
    def test_retrieval_error_message(self):
        err = DatasetMetadataRetrievalError("surv1", "per1", 500)
        assert "surv1" in str(err)
        assert "per1" in str(err)
        assert "500" in str(err)

    def test_create_error_message(self):
        err = DatasetCreateError(404)
        assert "404" in str(err)

    def test_retrieval_error_is_exception(self):
        with pytest.raises(DatasetMetadataRetrievalError):
            raise DatasetMetadataRetrievalError("s", "p", 500)


class TestSchemaPublishErrors:
    def test_schema_publish_error_attributes(self):
        err = SchemaPublishError("MyType", "Some message", "/path/to/file")
        assert err.error_type == "MyType"
        assert err.message == "Some message"
        assert err.filepath == "/path/to/file"

    def test_schema_publish_error_str_contains_error_message(self):
        err = SchemaPublishError("MyType", "Some message", "/path/to/file")
        assert "MyType" in str(err)
        assert "Some message" in str(err)
        assert "/path/to/file" in str(err)

    def test_generate_message_content_is_valid_json(self):
        err = SchemaPublishError("T", "M", "/f")
        content = json.loads(err.generate_message_content())
        assert content["error_type"] == "T"
        assert content["message"] == "M"
        assert content["filepath"] == "/f"

    @pytest.mark.parametrize("cls", [
        FilepathError,
        SchemaDuplicationError,
        SchemaVersionMismatchError,
        SurveyIDError,
        SchemaVersionError,
        SchemaJSONDecodeError,
    ])
    def test_single_filepath_errors(self, cls):
        err = cls("/my/path.json")
        assert err.filepath == "/my/path.json"
        assert isinstance(err, SchemaPublishError)
        assert isinstance(err, Exception)
        assert "/my/path.json" in str(err)

    def test_schema_fetch_error(self):
        err = SchemaFetchError("/path.json", 404, "https://example.com/path.json")
        assert "404" in err.message
        assert "https://example.com" in err.message
        assert "404" in str(err)

    def test_schema_post_error_includes_status_code(self):
        err = SchemaPostError("/path.json", 500)
        assert err.filepath == "/path.json"
        assert "500" in err.message
        assert "500" in str(err)

    def test_schema_metadata_error(self):
        err = SchemaMetadataError("survey_1", 503)
        assert "survey_1" in err.message
        assert "503" in err.message
        assert "survey_1" in str(err)

    def test_secret_access_error(self):
        err = SecretAccessError("some gcp error")
        assert isinstance(err, SdsAuthError)
        assert not isinstance(err, SchemaPublishError)
        assert "some gcp error" in str(err)

    def test_secret_key_error(self):
        err = SecretKeyError()
        assert isinstance(err, SdsAuthError)
        assert not isinstance(err, SchemaPublishError)
        assert "OAuth client ID" in str(err)

    def test_schema_metadata_format_error(self):
        err = SchemaMetadataFormatError("surv1")
        assert err.survey_id == "surv1"
        assert "surv1" in str(err)
        assert isinstance(err, SchemaPublishError)
        import json
        content = json.loads(err.generate_message_content())
        assert content["error_type"] == "SchemaMetadataFormatError"
