from __future__ import annotations
from enum import Enum


class Bucket(str, Enum):
    """
    Bucket enum representing Google Cloud Storage bucket names used in the SDS system.
    """

    SCHEMA_PUBLISH_BUCKET = 'schema_publish_bucket'
    DATASET_BUCKET = 'dataset_bucket'
