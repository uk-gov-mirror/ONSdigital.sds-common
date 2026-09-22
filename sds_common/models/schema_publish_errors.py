from __future__ import annotations
import json


class SchemaPublishError(Exception):
    def __init__(self, error_type: str, message: str, filepath: str):
        self.error_type = error_type
        self.message = message
        self.filepath = filepath
        self.error_message = f"Schema Publish Error - {self.error_type}: {self.message} Filepath: {self.filepath}"
        super().__init__(self.error_message)

    def generate_message_content(self) -> str:
        """
        Generates a JSON formatted string message from the error.

        :return: str: JSON formatted string message.
        """
        return json.dumps(
            {
                "error_type": self.error_type,
                "message": self.message,
                "filepath": self.filepath,
            }
        )


class FilepathError(SchemaPublishError):
    def __init__(self, filepath: str):
        super().__init__(
            error_type="FilepathError",
            message="Failed to split filename from path.",
            filepath=filepath,
        )


class SchemaDuplicationError(SchemaPublishError):
    def __init__(self, filepath: str):
        super().__init__(
            error_type="SchemaDuplicationError",
            message="Schema version already exists in SDS for new schema.",
            filepath=filepath,
        )


class SchemaVersionMismatchError(SchemaPublishError):
    def __init__(self, filepath: str):
        super().__init__(
            error_type="SchemaVersionMismatchError",
            message="Schema version does not match filename.",
            filepath=filepath,
        )


class SurveyIDError(SchemaPublishError):
    def __init__(self, filepath: str):
        super().__init__(
            error_type="SurveyIdError",
            message="Failed to fetch survey_id from schema JSON. Check the schema JSON contains a survey ID.",
            filepath=filepath,
        )


class SchemaVersionError(SchemaPublishError):
    def __init__(self, filepath: str):
        super().__init__(
            error_type="SchemaVersionError",
            message="Failed to fetch schema_version from schema JSON. Check the schema JSON contains a schema version.",
            filepath=filepath,
        )


class SchemaJSONDecodeError(SchemaPublishError):
    def __init__(self, filepath: str):
        super().__init__(
            error_type="SchemaJSONDecodeError",
            message="Failed to decode the downloaded schema as JSON.",
            filepath=filepath,
        )


class SchemaFetchError(SchemaPublishError):
    def __init__(self, filepath: str, status_code: int, url: str):
        super().__init__(
            error_type="SchemaFetchError",
            message=f"Failed to fetch schema from GitHub. Status code: {status_code}. URL: {url}",
            filepath=filepath,
        )


class SchemaPostError(SchemaPublishError):
    def __init__(self, filepath: str, status_code: int):
        super().__init__(
            error_type="SchemaPostError",
            message=f"Failed to post schema. Status code: {status_code}",
            filepath=filepath,
        )


class SchemaMetadataError(SchemaPublishError):
    def __init__(self, survey_id: str, status_code: int):
        super().__init__(
            error_type="SchemaMetadataError",
            message=f"Failed to fetch schema metadata for survey {survey_id}. Status code: {status_code}",
            filepath="N/A",
        )


class SchemaMetadataFormatError(SchemaPublishError):
    """Raised when the schema metadata response body is not in the expected list format."""

    def __init__(self, survey_id: str) -> None:
        self.survey_id = survey_id
        super().__init__(
            error_type="SchemaMetadataFormatError",
            message=(
                f"Schema metadata response for survey '{survey_id}' was not a list. "
                "This indicates an unexpected API contract change."
            ),
            filepath="N/A",
        )
