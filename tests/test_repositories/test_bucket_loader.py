"""Tests for BucketLoader."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from google.cloud import exceptions

from sds_common.enums.buckets import Bucket
from sds_common.repositories.bucket_loader import BucketLoader


@pytest.fixture
def storage_client():
    return MagicMock()


@pytest.fixture
def bucket_loader(storage_client):
    cfg = MagicMock()
    cfg.SCHEMA_PUBLISH_BUCKET_NAME = "proj-schema-publish"
    cfg.DATASET_BUCKET_NAME = "proj-dataset"
    return BucketLoader(storage_client=storage_client, config=cfg)


class TestBucketLoader:
    def test_fetch_bucket_returns_bucket(self, bucket_loader, storage_client):
        mock_bucket = MagicMock()
        storage_client.get_bucket.return_value = mock_bucket
        result = bucket_loader.fetch_bucket(Bucket.SCHEMA_PUBLISH_BUCKET)
        assert result is mock_bucket
        storage_client.get_bucket.assert_called_once_with("proj-schema-publish")

    def test_fetch_bucket_caches_result(self, bucket_loader, storage_client):
        mock_bucket = MagicMock()
        storage_client.get_bucket.return_value = mock_bucket
        r1 = bucket_loader.fetch_bucket(Bucket.SCHEMA_PUBLISH_BUCKET)
        r2 = bucket_loader.fetch_bucket(Bucket.SCHEMA_PUBLISH_BUCKET)
        assert r1 is r2
        assert storage_client.get_bucket.call_count == 1

    def test_fetch_bucket_raises_on_not_found(self, bucket_loader, storage_client):
        from unittest.mock import patch
        from sds_common.models.storage_errors import BucketNotFoundError
        storage_client.get_bucket.side_effect = exceptions.NotFound("not found")
        with patch("sds_common.repositories.bucket_loader.logger") as mock_logger:
            with pytest.raises(BucketNotFoundError) as exc_info:
                bucket_loader.fetch_bucket(Bucket.SCHEMA_PUBLISH_BUCKET)
        assert "proj-schema-publish" in str(exc_info.value)
        mock_logger.warning.assert_called_once()
        assert isinstance(exc_info.value.__cause__, exceptions.NotFound)

    def test_fetch_bucket_raises_on_wrong_type(self, bucket_loader):
        with pytest.raises(TypeError):
            bucket_loader.fetch_bucket("not-an-enum")

    def test_resolve_bucket_name_schema(self, bucket_loader):
        assert bucket_loader.resolve_bucket_name(Bucket.SCHEMA_PUBLISH_BUCKET) == "proj-schema-publish"

    def test_resolve_bucket_name_dataset(self, bucket_loader):
        assert bucket_loader.resolve_bucket_name(Bucket.DATASET_BUCKET) == "proj-dataset"

    def test_resolve_bucket_name_schema_publish(self, bucket_loader):
        assert bucket_loader.resolve_bucket_name(Bucket.SCHEMA_PUBLISH_BUCKET) == "proj-schema-publish"

    def test_each_bucket_enum_maps_correctly(self, bucket_loader, storage_client):
        for bucket in Bucket:
            storage_client.get_bucket.return_value = MagicMock()
            bucket_loader._bucket_cache.clear()
            bucket_loader.fetch_bucket(bucket)
            storage_client.get_bucket.assert_called()
