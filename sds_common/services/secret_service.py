from __future__ import annotations

import json
import logging
from typing import Any

from google.api_core.exceptions import GoogleAPICallError, RetryError

from sds_common.config.config import Config, get_config
from sds_common.models.auth_errors import SecretAccessError, SecretKeyError

logger = logging.getLogger(__name__)


class SecretService:
    def __init__(
        self,
        config: Config | None = None,
        client: Any | None = None,
    ) -> None:
        config = config or get_config()
        self.project_id = config.PROJECT_ID
        self.secret_id = config.SECRET_ID
        self.client = client or self._create_client()

    def get_oauth_client_id(self) -> str:
        """
        Get the OAuth client ID for authenticating with SDS.

        :return: the OAuth client ID.
        :raises SecretKeyError: If the client ID key is not found in the secret.
        """
        try:
            secret = self._get_secret_version()
            secret_json = json.loads(secret)
            return secret_json['web']['client_id']
        except KeyError as error:
            logger.warning(
                "OAuth client ID key not found in secret '%s'. Missing key: %s",
                self.secret_id, error, exc_info=True,
            )
            raise SecretKeyError() from error

    def _get_secret_version(self) -> str:
        """
        Access the latest secret version from Google Cloud Secret Manager.

        :return: The Secret value.
        :raises SecretAccessError: If unable to access the secret version.
        """
        try:
            name = f'projects/{self.project_id}/secrets/{self.secret_id}/versions/latest'
            response = self.client.access_secret_version(name=name)
            return response.payload.data.decode('UTF-8')
        except (GoogleAPICallError, RetryError) as error:
            logger.warning(
                "Failed to access secret '%s' in project '%s': %s",
                self.secret_id, self.project_id, error, exc_info=True,
            )
            raise SecretAccessError(str(error)) from error

    @staticmethod
    def _create_client() -> Any:
        try:
            from google.cloud.secretmanager import SecretManagerServiceClient
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError('google-cloud-secret-manager must be installed to use SecretService.') from error
        return SecretManagerServiceClient()
