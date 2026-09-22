from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

from sds_common.config.config_helpers import ConfigHelpers


class Config:
    def __init__(self) -> None:
        self.PROJECT_ID = cast(str, ConfigHelpers.get_value_from_env('PROJECT_ID', 'ons-sds-sandbox'))
        self.SDS_URL = cast(str, ConfigHelpers.get_value_from_env('SDS_URL'))
        self.LOADER_URL = cast(str, ConfigHelpers.get_value_from_env('SDS_LOADER_URL'))
        self.PROCESS_TIMEOUT = int(ConfigHelpers.get_value_from_env('HTTP_REQUEST_TIMEOUT_SECONDS', '540'))
        self.SECRET_ID = cast(str, ConfigHelpers.get_value_from_env('IAP_SECRET_ID', 'iap-secret'))
        self.GITHUB_SCHEMA_URL = cast(
            str,
            ConfigHelpers.get_value_from_env(
                'GITHUB_SCHEMA_BASE_URL',
                'https://raw.githubusercontent.com/ONSdigital/sds-schema-definitions/main/',
            ),
        )
        self.POST_SCHEMA_ENDPOINT = cast(str, ConfigHelpers.get_value_from_env('POST_SCHEMA_PATH', '/schemas'))
        self.GET_SCHEMA_METADATA_ENDPOINT = cast(
            str,
            ConfigHelpers.get_value_from_env('GET_SCHEMA_METADATA_PATH', '/schemas/metadata'),
        )
        self.GET_ALL_SCHEMA_METADATA_ENDPOINT = cast(
            str,
            ConfigHelpers.get_value_from_env('GET_ALL_SCHEMA_METADATA_PATH', '/schemas/all-metadata'),
        )
        self.GET_DATASET_METADATA_ENDPOINT = cast(
            str,
            ConfigHelpers.get_value_from_env('GET_DATASET_METADATA_PATH', '/datasets/metadata'),
        )
        self.DATASET_CREATE_ENDPOINT = cast(
            str,
            ConfigHelpers.get_value_from_env('DATASET_CREATE_PATH', '/events/dataset/create'),
        )
        self.DATASET_DELETE_ENDPOINT = cast(
            str,
            ConfigHelpers.get_value_from_env('DATASET_DELETE_PATH', '/events/dataset/delete'),
        )
        self.PUBLISH_SCHEMA_ERROR_TOPIC_ID = cast(
            str,
            ConfigHelpers.get_value_from_env('PUBLISH_SCHEMA_ERROR_TOPIC_ID', 'ons-sds-publish-schema-fail'),
        )
        self.PUBLISH_SCHEMA_SUCCESS_TOPIC_ID = cast(
            str,
            ConfigHelpers.get_value_from_env('PUBLISH_SCHEMA_SUCCESS_TOPIC_ID', 'ons-sds-publish-schema'),
        )
        self.PUBLISH_SCHEMA_QUEUE_TOPIC_ID = cast(
            str,
            ConfigHelpers.get_value_from_env('PUBLISH_SCHEMA_QUEUE_TOPIC_ID', 'schema-publish-queue'),
        )
        self.PUBLISH_DATASET_TOPIC_ID = cast(
            str,
            ConfigHelpers.get_value_from_env('PUBLISH_DATASET_TOPIC_ID', 'ons-sds-publish-dataset'),
        )
        self.FIRESTORE_DB_NAME = cast(
            str,
            ConfigHelpers.get_value_from_env('FIRESTORE_DB_NAME', f'{self.PROJECT_ID}-sds'),
        )
        self.SCHEMA_PUBLISH_BUCKET_NAME = cast(
            str,
            ConfigHelpers.get_value_from_env(
                'SCHEMA_STAGING_BUCKET_NAME',
                f'{self.PROJECT_ID}-sds-europe-west2-schema-publish',
            ),
        )
        self.DATASET_BUCKET_NAME = cast(
            str,
            ConfigHelpers.get_value_from_env('DATASET_BUCKET_NAME', f'{self.PROJECT_ID}-sds-europe-west2-dataset'),
        )


@lru_cache(maxsize=1)
def get_config() -> Config:
    """
    Return the cached singleton Config instance, constructing it on first call.

    :return Config: The application configuration.
    """
    return Config()


class _LazyConfigProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_config(), name)

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(dir(get_config())))

    def __repr__(self) -> str:
        return repr(get_config())


CONFIG = cast(Config, _LazyConfigProxy())
