"""Tests for SchemaValidatorService."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from sds_common.models.schema_publish_errors import (
    SchemaMetadataFormatError,
    SchemaDuplicationError,
    SchemaVersionMismatchError,
)
from sds_common.schema.schema import Schema
from sds_common.services.schema_validator_service import SchemaValidatorService


class TestSchemaValidatorService:
    def _svc(self, metadata_return_value):
        schema_req_svc = MagicMock()
        schema_req_svc.get_metadata.return_value = metadata_return_value
        return SchemaValidatorService(schema_request_service=schema_req_svc)

    def test_validate_passes_when_version_matches_and_no_duplicates(self):
        svc = self._svc([{"schema_version": "v2"}])
        schema = Schema({}, "surv1", "v1", "v1.json")
        svc.validate(schema)  # should not raise

    def test_validate_passes_for_new_survey_none_return(self):
        """get_metadata returns None (404) for a brand-new survey."""
        svc = self._svc(None)
        schema = Schema({}, "surv1", "v1", "v1.json")
        svc.validate(schema)

    def test_validate_raises_version_mismatch(self):
        svc = self._svc([])
        schema = Schema({}, "surv1", "v1", "different_name.json")
        with pytest.raises(SchemaVersionMismatchError):
            svc.validate(schema)

    def test_validate_raises_duplication_error(self):
        svc = self._svc([{"schema_version": "v1"}])
        schema = Schema({}, "surv1", "v1", "v1.json")
        with pytest.raises(SchemaDuplicationError):
            svc.validate(schema)

    def test_verify_version_static_happy_path(self):
        schema = Schema({}, "surv1", "v1", "v1.json")
        SchemaValidatorService._verify_version(schema)

    def test_verify_version_static_raises_on_mismatch(self):
        schema = Schema({}, "surv1", "v1", "v2.json")
        with pytest.raises(SchemaVersionMismatchError):
            SchemaValidatorService._verify_version(schema)

    def test_check_duplicate_versions_raises_format_error_on_non_list(self):
        """When the API returns 200 but body is not a list, SchemaMetadataFormatError is raised."""
        schema_req_svc = MagicMock()
        schema_req_svc.get_metadata.return_value = {"error": "unexpected"}  # dict not list
        svc = SchemaValidatorService(schema_request_service=schema_req_svc)
        schema = Schema({}, "surv1", "v1", "v1.json")
        with pytest.raises(SchemaMetadataFormatError) as exc_info:
            svc._check_duplicate_versions(schema)
        assert "surv1" in str(exc_info.value)

    def test_schema_metadata_format_error_is_schema_publish_error(self):
        """SchemaMetadataFormatError is a SchemaPublishError — it can be published to Pub/Sub."""
        from sds_common.models.schema_publish_errors import SchemaPublishError
        err = SchemaMetadataFormatError("surv1")
        assert isinstance(err, SchemaPublishError)
        assert err.survey_id == "surv1"
        assert "surv1" in str(err)
        assert err.generate_message_content() is not None
