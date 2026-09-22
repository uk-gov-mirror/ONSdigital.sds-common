from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from sds_common.services.sds_schema_request_service import SdsSchemaRequestService


class SchemaPublisher(ABC):
    """
    Abstract base class for schema publishers.
    """

    def __init__(self, schema_request_service: SdsSchemaRequestService) -> None:
        self.schema_request_service = schema_request_service

    @abstractmethod
    def _retrieve_schema(self, filename: str) -> dict:
        """
        Retrieves the schema for the given file name.

        :param filename: The name of the schema file to be retrieved.
        :return: The schema as a dictionary.
        """
        ...  # pragma: no cover

    @abstractmethod
    def publish(self, filename: str) -> requests.Response:
        """
        Publishes the schema for the given file name.

        :param filename: The name of the schema file to be published.
        :return: The response from the schema publishing service.
        """
        ...  # pragma: no cover
