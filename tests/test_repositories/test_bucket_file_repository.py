"""Tests for BucketFileRepository."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

from sds_common.repositories.bucket_file_repository import BucketFileRepository


def _make_bucket():
    return MagicMock()


class TestBucketFileRepository:
    def test_get_file_as_json(self):
        bucket = _make_bucket()
        blob = MagicMock()
        blob.download_as_string.return_value = json.dumps({"key": "val"}).encode()
        bucket.blob.return_value = blob
        repo = BucketFileRepository(bucket)
        result = repo.get_file_as_json("myfile.json")
        assert result == {"key": "val"}
        bucket.blob.assert_called_once_with("myfile.json")

    def test_upload_file_from_path(self, tmp_path):
        bucket = _make_bucket()
        blob = MagicMock()
        bucket.blob.return_value = blob
        filepath = str(tmp_path / "upload.json")
        open(filepath, "w").write("{}")
        repo = BucketFileRepository(bucket)
        repo.upload_file_from_path(filepath)
        bucket.blob.assert_called_once_with("upload.json")
        blob.upload_from_filename.assert_called_once_with(filepath)

    def test_delete_file(self):
        bucket = _make_bucket()
        blob = MagicMock()
        bucket.blob.return_value = blob
        repo = BucketFileRepository(bucket)
        repo.delete_file("delete_me.json")
        bucket.blob.assert_called_once_with("delete_me.json")
        blob.delete.assert_called_once()

    def test_check_file_exists_true(self):
        bucket = _make_bucket()
        blob = MagicMock()
        blob.exists.return_value = True
        bucket.blob.return_value = blob
        repo = BucketFileRepository(bucket)
        assert repo.check_file_exists("present.json") is True

    def test_check_file_exists_false(self):
        bucket = _make_bucket()
        blob = MagicMock()
        blob.exists.return_value = False
        bucket.blob.return_value = blob
        repo = BucketFileRepository(bucket)
        assert repo.check_file_exists("absent.json") is False
