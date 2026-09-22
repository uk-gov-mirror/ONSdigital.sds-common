from sds_common.config.config import CONFIG, Config, get_config
from sds_common.config.logging_config import GcpJsonFormatter, configure_gcp_logging
from sds_common.enums.buckets import Bucket
from sds_common.models.auth_errors import SdsAuthError, SecretAccessError, SecretKeyError
from sds_common.models.config_errors import EnvironmentVariableError
from sds_common.models.dataset_models import DatasetMetadata
from sds_common.models.dataset_publish_errors import (
    DatasetCreateError,
    DatasetMetadataRetrievalError,
    DatasetPublishError,
)
from sds_common.models.schema_publish_errors import (
    FilepathError,
    SchemaDuplicationError,
    SchemaFetchError,
    SchemaJSONDecodeError,
    SchemaMetadataError,
    SchemaMetadataFormatError,
    SchemaPostError,
    SchemaPublishError,
    SchemaVersionError,
    SchemaVersionMismatchError,
    SurveyIDError,
)
from sds_common.models.storage_errors import BucketNotFoundError
from sds_common.sds_common import SdsCommon
from sds_common.test_helpers.pub_sub_helper import PubSubHelper

__all__ = [
    # Entry point
    'SdsCommon',

    # Configuration
    'Config',
    'CONFIG',
    'get_config',

    # Logging
    'configure_gcp_logging',
    'GcpJsonFormatter',

    # Data models
    'Bucket',
    'DatasetMetadata',

    # Errors — authentication
    'SdsAuthError',
    'SecretAccessError',
    'SecretKeyError',

    # Errors — schema publishing
    'SchemaPublishError',
    'FilepathError',
    'SchemaDuplicationError',
    'SchemaFetchError',
    'SchemaJSONDecodeError',
    'SchemaMetadataError',
    'SchemaMetadataFormatError',
    'SchemaPostError',
    'SchemaVersionError',
    'SchemaVersionMismatchError',
    'SurveyIDError',

    # Errors — dataset publishing
    'DatasetPublishError',
    'DatasetCreateError',
    'DatasetMetadataRetrievalError',

    # Errors — infrastructure
    'BucketNotFoundError',
    'EnvironmentVariableError',

    # Test helpers (intentionally standalone)
    'PubSubHelper',
]
