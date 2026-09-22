from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests  # pragma: no cover

from google.cloud import firestore, storage
from google.cloud.pubsub_v1 import PublisherClient

from sds_common.config.config import Config, get_config
from sds_common.enums.buckets import Bucket
from sds_common.publishers.gcs_schema_publisher import GcsSchemaPublisher
from sds_common.publishers.github_schema_publisher import GithubSchemaPublisher
from sds_common.repositories.bucket_file_repository import BucketFileRepository
from sds_common.repositories.bucket_loader import BucketLoader
from sds_common.services.auth_header_provider import AuthHeaderProvider
from sds_common.services.file_service import FileService
from sds_common.services.http_service import HttpService
from sds_common.services.pub_sub_service import PubSubService
from sds_common.services.schema_validator_service import SchemaValidatorService
from sds_common.services.sds_dataset_request_service import SdsDatasetRequestService
from sds_common.services.sds_schema_request_service import SdsSchemaRequestService
from sds_common.services.secret_service import SecretService
from sds_common.test_helpers.firebase_loader import FirebaseLoader


class SdsCommon:
    """
    Facade providing lazy, dependency-injected access to all SDS common services.

    Instantiate once and access only the services you need — nothing is created
    until first access.

    Example::

        client = SdsCommon()

        # Only iap_auth + _secrets are instantiated:
        headers = client.iap_auth.generate()

        # Fully authenticated SDS schema request:
        client.schemas.get_metadata("my_survey")
    """

    def __init__(self, config: Config | None = None) -> None:
        self._config = config

    # ------------------------------------------------------------------ config

    @cached_property
    def config(self) -> Config:
        """Resolved configuration — uses injected config or the global cached singleton."""
        return self._config or get_config()

    # ----------------------------------------------------------- core services

    @cached_property
    def _secrets(self) -> SecretService:
        """GCP Secret Manager client — reads IAP OAuth credentials."""
        return SecretService(config=self.config)

    @cached_property
    def iap_auth(self) -> AuthHeaderProvider:
        """Generates IAP Bearer-token authentication headers."""
        return AuthHeaderProvider(
            secret_service=self._secrets,
            config=self.config,
        )

    # ------------------------------------------------------------ http clients

    @cached_property
    def _http(self) -> HttpService:
        """Unauthenticated HTTP client — for requests that do not require IAP (e.g. GitHub)."""
        return HttpService.create()

    @property
    def _authenticated_http(self) -> HttpService:
        """
        Authenticated HTTP client — generates a fresh IAP token on every access.

        IAP tokens are short-lived (~1 hour). Using a ``@property`` rather than
        ``@cached_property`` ensures the token is never stale.  The underlying
        session (with its retry adapter) is still reused via the cached
        ``_authenticated_session``.
        """
        headers = self.iap_auth.generate()
        return HttpService(session=self._authenticated_session, headers=headers)

    @cached_property
    def _authenticated_session(self) -> requests.Session:
        """Long-lived retry session shared by all authenticated requests."""
        return HttpService._build_session()

    # -------------------------------------------------------- storage / pubsub

    @cached_property
    def _schema_staging_files(self) -> FileService:
        """File operations on the schema staging GCS bucket (schemas awaiting publish)."""
        return self._build_file_service(Bucket.SCHEMA_PUBLISH_BUCKET)

    @cached_property
    def _dataset_files(self) -> FileService:
        """File operations on the dataset GCS bucket."""
        return self._build_file_service(Bucket.DATASET_BUCKET)

    @cached_property
    def pub_sub(self) -> PubSubService:
        """GCP Pub/Sub publisher."""
        return PubSubService(
            publisher_client=PublisherClient(),
            project_id=self.config.PROJECT_ID,
        )

    # ----------------------------------------------------- SDS request services

    @cached_property
    def schemas(self) -> SdsSchemaRequestService:
        """HTTP client for SDS schema endpoints (metadata, post).
        
        Generates fresh authentication headers on each request, ensuring tokens
        never expire during the lifetime of a long-lived SdsCommon instance.
        """
        return SdsSchemaRequestService(
            http_service=self._http,
            config=self.config,
            auth_header_generator=self.iap_auth.generate,
        )

    @cached_property
    def datasets(self) -> SdsDatasetRequestService:
        """HTTP client for SDS dataset endpoints (metadata).
        
        Generates fresh authentication headers on each request, ensuring tokens
        never expire during the lifetime of a long-lived SdsCommon instance.
        """
        return SdsDatasetRequestService(
            http_service=self._http,
            config=self.config,
            auth_header_generator=self.iap_auth.generate,
        )

    # ------------------------------------------------------------ publishers

    @cached_property
    def _schema_validator(self) -> SchemaValidatorService:
        """Validates a schema against existing SDS metadata before publishing."""
        return SchemaValidatorService(self.schemas)

    @cached_property
    def gcs_publisher(self) -> GcsSchemaPublisher:
        """Publishes schemas from the GCS staging bucket to SDS."""
        return GcsSchemaPublisher(
            schema_request_service=self.schemas,
            file_service=self._schema_staging_files,
        )

    @cached_property
    def github_publisher(self) -> GithubSchemaPublisher:
        """Fetches schemas from GitHub, validates, and publishes to SDS."""
        return GithubSchemaPublisher(
            schema_request_service=self.schemas,
            validator_service=self._schema_validator,
            github_schema_url=self.config.GITHUB_SCHEMA_URL,
            http_service=self._http,
        )

    # ------------------------------------------------------ firestore

    @cached_property
    def _firestore_client(self) -> firestore.Client:
        """Raw Firestore client."""
        return firestore.Client(
            project=self.config.PROJECT_ID,
            database=self.config.FIRESTORE_DB_NAME,
        )

    @cached_property
    def firestore(self) -> FirebaseLoader:
        """Typed Firestore wrapper with pre-loaded schema collection."""
        return FirebaseLoader(self._firestore_client)


    # ---------------------------------------------------------------- internal

    def _build_file_service(self, bucket: Bucket) -> FileService:
        bucket_loader = BucketLoader(
            storage_client=storage.Client(project=self.config.PROJECT_ID),
            config=self.config,
        )
        bucket_instance = bucket_loader.fetch_bucket(bucket)
        return FileService(BucketFileRepository(bucket_instance))
