from __future__ import annotations

import requests

from sds_common.publishers.schema_publisher import SchemaPublisher
from sds_common.schema.schema import Schema
from sds_common.services.file_service import FileService
from sds_common.services.sds_schema_request_service import SdsSchemaRequestService


class GcsSchemaPublisher(SchemaPublisher):
    """
    Publisher for retrieving and publishing schemas from Google Cloud Storage (GCS) buckets.
    """

    def __init__(self, schema_request_service: SdsSchemaRequestService, file_service: FileService) -> None:
        super().__init__(schema_request_service)
        self.file_service = file_service

    def _retrieve_schema(self, filename: str) -> dict:
        """
        Retrieve the schema JSON file from the GCS bucket.

        :param filename: The name of the schema file to retrieve.
        :return: The schema as a dictionary.
        """
        return self.file_service.get_json(filename)

    def publish(self, filename: str) -> requests.Response:
        """
        Publish the schema retrieved from the GCS bucket.

        On success, the staged file is automatically deleted from the bucket.
        On failure (any exception), the file is left in place for inspection/retry.

        .. warning::
            If your consumer processes staged files in order (e.g. oldest-first),
            a persistently failing file will block newer files from being published.
            See the publisher documentation for guidance on handling stuck files.

        :param filename: The name of the schema file to publish.
        :return: The response from the schema publishing service.
        """
        schema_json = self._retrieve_schema(filename)
        schema = Schema.set_schema(schema_json, filename)
        response = self.schema_request_service.publish(schema.json, schema.filepath)
        self.file_service.delete(filename)
        return response
