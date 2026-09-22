from __future__ import annotations

import logging
from typing import Callable

import requests

from sds_common.config.config import Config, get_config
from sds_common.models.schema_publish_errors import SchemaMetadataError, SchemaPostError
from sds_common.schema.schema import Schema
from sds_common.services.http_service import HttpService

logger = logging.getLogger(__name__)


class SdsSchemaRequestService:
    """
    Service to handle requests to SDS schema endpoints.
    
    Generates fresh authentication headers on each request by calling the
    provided ``auth_header_generator`` callable, ensuring tokens never expire.
    """

    def __init__(
        self,
        http_service: HttpService,
        config: Config | None = None,
        auth_header_generator: Callable[[], dict[str, str]] | None = None,
    ) -> None:
        self.http_service = http_service
        self.config = config or get_config()
        self.auth_header_generator = auth_header_generator

    def get_metadata(self, survey_id: str) -> list[dict] | None:
        """
        Call the GET /schemas/metadata SDS endpoint and return parsed metadata.

        :param survey_id: the survey_id of the schema.
        :return: list of schema metadata dicts, or ``None`` if the survey does not exist (404).
        :raises SchemaMetadataError: if the response status code is not 200 or 404.
        """
        url = f'{self.config.SDS_URL}{self.config.GET_SCHEMA_METADATA_ENDPOINT}'
        headers = self._get_fresh_headers()
        response = self.http_service.session.get(url, headers=headers, params={'survey_id': survey_id})
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            logger.warning(
                "Failed to fetch schema metadata for survey '%s'. Status: %d",
                survey_id, response.status_code,
            )
            raise SchemaMetadataError(survey_id, response.status_code)
        return response.json()

    def get_all_metadata(self) -> list[dict]:
        """
        Call the GET /schemas/all-metadata endpoint and return all schema metadata.

        :return: list of all schema metadata dicts.
        :raises SchemaMetadataError: if the response status code is not 200.
        """
        url = f'{self.config.SDS_URL}{self.config.GET_ALL_SCHEMA_METADATA_ENDPOINT}'
        headers = self._get_fresh_headers()
        response = self.http_service.session.get(url, headers=headers)
        if response.status_code != 200:
            logger.warning(
                "Failed to fetch all schema metadata. Status: %d",
                response.status_code,
            )
            raise SchemaMetadataError("all_schemas", response.status_code)
        return response.json()

    def publish(self, schema_json: dict, filepath: str = 'N/A') -> requests.Response:
        """
        Publish a schema dict to SDS.

        :param schema_json: the schema JSON to be published.
        :param filepath: optional filepath for use in error messages (e.g. the source filename).
        :return response: the response from the POST request.
        :raises SurveyIDError: if the schema JSON does not contain a survey_id.
        :raises SchemaVersionError: if the schema JSON does not contain a schema_version.
        :raises SchemaPostError: if SDS returns a non-200 response.
        """
        schema = Schema.set_schema(schema_json, filepath)
        logger.info('Publishing schema for survey %s', schema.survey_id)
        url = f'{self.config.SDS_URL}{self.config.POST_SCHEMA_ENDPOINT}'
        headers = self._get_fresh_headers()
        response = self.http_service.session.post(url, json=schema.json, headers=headers, params={'survey_id': schema.survey_id})
        if response.status_code != 200:
            logger.warning(
                "Failed to post schema '%s' for survey '%s'. Status: %d",
                schema.filepath, schema.survey_id, response.status_code,
            )
            raise SchemaPostError(schema.filepath, response.status_code)
        logger.info('Schema %s published for survey %s', schema.filepath, schema.survey_id)
        return response

    def _get_fresh_headers(self) -> dict[str, str] | None:
        """Generate fresh authentication headers for this request."""
        if self.auth_header_generator:
            return self.auth_header_generator()
        return None
