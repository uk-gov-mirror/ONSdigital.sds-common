from __future__ import annotations

from typing import Any

import google.auth.transport.requests
import google.oauth2.id_token

from sds_common.config.config import Config, get_config
from sds_common.services.secret_service import SecretService


class AuthHeaderProvider:
    """
    Generates IAP Bearer-token authentication headers for SDS requests.

    Two strategies are available:

    - :meth:`generate` — for GCP-hosted environments where the metadata server
      is reachable (Cloud Run, Cloud Functions, GCE, etc.).

    - :meth:`generate_by_impersonation` — for local development; impersonates
      the App Engine default service account via IAM. Requires the caller's ADC
      account to hold the ``Service Account Token Creator`` role.
    """

    def __init__(
        self,
        secret_service: SecretService,
        config: Config | None = None,
        iam_credentials_client: Any | None = None,
    ) -> None:
        self.secret_service = secret_service
        self.config = config or get_config()
        self.iam_credentials_client = iam_credentials_client

    def generate(self) -> dict[str, str]:
        """
        Create IAP authentication headers using the GCP metadata server.

        :return: A dict containing ``Authorization`` and ``Content-Type`` headers.
        """
        oauth_client_id = self.secret_service.get_oauth_client_id()
        auth_req = google.auth.transport.requests.Request()
        auth_token = google.oauth2.id_token.fetch_id_token(auth_req, audience=oauth_client_id)
        return {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json',
        }

    def generate_by_impersonation(self) -> dict[str, str]:
        """
        Create IAP authentication headers by impersonating the App Engine default service account.

        :return: A dict containing ``Authorization`` and ``Content-Type`` headers.
        """
        oauth_client_id = self.secret_service.get_oauth_client_id()
        impersonated_sa_email = f'{self.config.PROJECT_ID}@appspot.gserviceaccount.com'
        iam_client = self.iam_credentials_client or self._create_iam_credentials_client()
        resource_name = f'projects/-/serviceAccounts/{impersonated_sa_email}'

        response = iam_client.generate_id_token(
            name=resource_name,
            audience=oauth_client_id,
            include_email=True,
        )
        return {
            'Authorization': f'Bearer {response.token}',
            'Content-Type': 'application/json',
        }

    @staticmethod
    def _create_iam_credentials_client() -> Any:
        try:
            from google.cloud import iam_credentials_v1
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError('google-cloud-iam must be installed to use impersonation auth.') from error
        return iam_credentials_v1.IAMCredentialsClient()
