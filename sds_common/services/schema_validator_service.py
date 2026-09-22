from __future__ import annotations

import logging

from sds_common.models.schema_publish_errors import SchemaDuplicationError, SchemaMetadataFormatError, SchemaVersionMismatchError
from sds_common.schema.schema import Schema
from sds_common.services.sds_schema_request_service import SdsSchemaRequestService
from sds_common.utilities.utils import split_filename

logger = logging.getLogger(__name__)


class SchemaValidatorService:
    def __init__(self, schema_request_service: SdsSchemaRequestService) -> None:
        self.sds_schema_request_service = schema_request_service

    def validate(self, schema: Schema) -> None:
        """
        Validate the schema by verifying the version and checking for duplicate versions.

        :param schema: The schema object to validate.
        """
        logger.info('Validating schema %s', schema.filepath)
        self._verify_version(schema)
        self._check_duplicate_versions(schema)

    @staticmethod
    def _verify_version(schema: Schema) -> None:
        """
        Verifies that the schema version in the JSON matches the filename.

        :param schema: the schema object to be posted.
        :raises SchemaVersionMismatchError: if the schema version does not match the filename.
        """
        trimmed_filename = split_filename(schema.filepath)
        if schema.schema_version != trimmed_filename:
            raise SchemaVersionMismatchError(schema.filepath)

    def _check_duplicate_versions(self, schema: Schema) -> None:
        """
        Check that the schema_version for the new schema is not already present in SDS.

        :param schema: the schema to be posted.
        :raises SchemaDuplicationError: if the schema version already exists in SDS.
        :raises SchemaMetadataFormatError: if the metadata response body is not a list.
        """
        metadata = self.sds_schema_request_service.get_metadata(schema.survey_id)

        if metadata is None:
            return

        if not isinstance(metadata, list):
            raise SchemaMetadataFormatError(schema.survey_id)

        for version in metadata:
            if schema.schema_version == version['schema_version']:
                raise SchemaDuplicationError(schema.filepath)
