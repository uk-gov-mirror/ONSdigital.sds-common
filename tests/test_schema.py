"""Tests for Schema class."""
from __future__ import annotations

import pytest

from sds_common.models.schema_publish_errors import SchemaVersionError, SurveyIDError
from sds_common.schema.schema import Schema


VALID_JSON = {
    "properties": {
        "survey_id": {"enum": ["survey_abc"]},
        "schema_version": {"const": "v2"},
    }
}


class TestSchema:
    def test_direct_construction(self):
        s = Schema(VALID_JSON, "survey_abc", "v2", "v2.json")
        assert s.survey_id == "survey_abc"
        assert s.schema_version == "v2"
        assert s.filepath == "v2.json"
        assert s.json is VALID_JSON

    def test_set_schema_happy_path(self):
        s = Schema.set_schema(VALID_JSON, "schemas/v2.json")
        assert s.survey_id == "survey_abc"
        assert s.schema_version == "v2"
        assert s.filepath == "schemas/v2.json"

    def test_set_schema_raises_survey_id_error_when_key_missing(self):
        bad = {"properties": {"schema_version": {"const": "v1"}}}
        with pytest.raises(SurveyIDError) as exc_info:
            Schema.set_schema(bad, "v1.json")
        assert exc_info.value.__cause__ is not None  # original KeyError chained

    def test_set_schema_raises_survey_id_error_when_enum_empty(self):
        bad = {"properties": {"survey_id": {"enum": []}, "schema_version": {"const": "v1"}}}
        with pytest.raises(SurveyIDError) as exc_info:
            Schema.set_schema(bad, "v1.json")
        assert exc_info.value.__cause__ is not None  # original IndexError chained

    def test_set_schema_raises_schema_version_error_when_key_missing(self):
        bad = {"properties": {"survey_id": {"enum": ["s1"]}}}
        with pytest.raises(SchemaVersionError) as exc_info:
            Schema.set_schema(bad, "v1.json")
        assert exc_info.value.__cause__ is not None  # original KeyError chained

    def test_get_survey_id_from_json(self):
        result = Schema._get_survey_id_from_json(VALID_JSON)
        assert result == "survey_abc"

    def test_get_schema_version_from_json(self):
        result = Schema._get_schema_version_from_json(VALID_JSON)
        assert result == "v2"
