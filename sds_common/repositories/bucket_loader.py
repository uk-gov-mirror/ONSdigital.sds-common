from __future__ import annotations

import logging

from google.cloud import exceptions, storage

from sds_common.config.config import Config, get_config
from sds_common.enums.buckets import Bucket
from sds_common.models.storage_errors import BucketNotFoundError

logger = logging.getLogger(__name__)

_BUCKET_CONFIG_MAP = {
    Bucket.SCHEMA_PUBLISH_BUCKET: 'SCHEMA_PUBLISH_BUCKET_NAME',
    Bucket.DATASET_BUCKET: 'DATASET_BUCKET_NAME',
}


class BucketLoader:
    def __init__(self, storage_client: storage.Client, config: Config | None = None) -> None:
        self._client = storage_client
        self.config = config or get_config()
        self._bucket_cache: dict[Bucket, storage.Bucket] = {}

    def resolve_bucket_name(self, bucket: Bucket) -> str:
        """
        Returns the GCS bucket name for the given Bucket enum value.

        :param bucket: The Bucket enum value.
        :return str: The configured bucket name.
        :raises TypeError: If the provided value is not a Bucket enum instance.
        """
        if not isinstance(bucket, Bucket):
            raise TypeError(f'Expected bucket to be an instance of Bucket enum, got {type(bucket)}')
        return getattr(self.config, _BUCKET_CONFIG_MAP[bucket])

    def fetch_bucket(self, bucket: Bucket) -> storage.Bucket:
        """
        Lazily fetches and caches the specified bucket from Google Cloud Storage.

        :param bucket: An instance of the Bucket enum representing the desired bucket.
        :return: The Google Cloud Storage Bucket instance.
        :raises TypeError: If the provided bucket is not an instance of the Bucket enum.
        :raises BucketNotFoundError: If the specified bucket does not exist.
        """
        if bucket not in self._bucket_cache:
            bucket_name = self.resolve_bucket_name(bucket)
            try:
                self._bucket_cache[bucket] = self._client.get_bucket(bucket_name)
            except exceptions.NotFound as exc:
                logger.warning("Bucket '%s' not found in Google Cloud Storage.", bucket_name, exc_info=True)
                raise BucketNotFoundError(bucket_name) from exc
        return self._bucket_cache[bucket]
