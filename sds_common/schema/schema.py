from __future__ import annotations

from sds_common.models.schema_publish_errors import (
    SchemaVersionError,
    SurveyIDError,
)


class Schema:
    def __init__(
        self, schema_json: dict, survey_id: str, schema_version: str, filepath: str
    ) -> None:
        self.json = schema_json
        self.filepath = filepath
        self.survey_id = survey_id
        self.schema_version = schema_version

    @classmethod
    def set_schema(cls, schema_json: dict, filepath: str) -> Schema:
        """
        Sets the schema object with the survey ID and schema version from the schema JSON.

        :param schema_json: the schema JSON.
        :param filepath: the path to the schema JSON.
        :return Schema: the schema object.
        :raises SurveyIDError: if the survey ID cannot be fetched from the schema JSON.
        :raises SchemaVersionError: if the schema version cannot be fetched from the schema JSON.
        """
        try:
            survey_id = cls._get_survey_id_from_json(schema_json)
        except (KeyError, IndexError) as error:
            raise SurveyIDError(filepath) from error

        try:
            schema_version = cls._get_schema_version_from_json(schema_json)
        except KeyError as error:
            raise SchemaVersionError(filepath) from error

        return cls(schema_json, survey_id, schema_version, filepath)

    @staticmethod
    def _get_survey_id_from_json(schema_json: dict) -> str:
        """
        Fetches the survey ID from the schema JSON.

        :param schema_json: the schema JSON.
        :return str: the survey ID.
        """
        return schema_json["properties"]["survey_id"]["enum"][0]

    @staticmethod
    def _get_schema_version_from_json(schema_json: dict) -> str:
        """
        Fetches the schema version from the schema JSON.

        :param schema_json: the schema JSON.
        :return str: the schema version.
        """
        return schema_json["properties"]["schema_version"]["const"]
