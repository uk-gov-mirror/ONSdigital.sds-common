"""Tests for FileService using FakeBucketFileRepository."""
from __future__ import annotations

import json

import pytest

from sds_common.services.file_service import FileService
from tests.fakes import FakeBucketFileRepository


SCHEMA_CONTENT = {"properties": {"survey_id": {"enum": ["s1"]}}}


@pytest.fixture
def repo():
    return FakeBucketFileRepository()


@pytest.fixture
def svc(repo):
    return FileService(bucket_repository=repo)


class TestFileService:
    def test_upload_stores_file_in_repo(self, svc, repo, tmp_path):
        filepath = tmp_path / "068_1.json"
        filepath.write_text(json.dumps(SCHEMA_CONTENT))
        svc.upload(str(filepath))
        assert repo.check_file_exists("068_1.json")
        assert repo.get_file_as_json("068_1.json") == SCHEMA_CONTENT

    def test_get_json_returns_file_content(self, svc, repo):
        repo.add("068_1.json", SCHEMA_CONTENT)
        result = svc.get_json("068_1.json")
        assert result == SCHEMA_CONTENT

    def test_get_json_raises_when_file_missing(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.get_json("missing.json")

    def test_delete_removes_file(self, svc, repo):
        repo.add("068_1.json", SCHEMA_CONTENT)
        svc.delete("068_1.json")
        assert not repo.check_file_exists("068_1.json")

    def test_delete_is_idempotent(self, svc):
        svc.delete("nonexistent.json")

    def test_exists_returns_true_when_present(self, svc, repo):
        repo.add("068_1.json", SCHEMA_CONTENT)
        assert svc.exists("068_1.json") is True

    def test_exists_returns_false_when_absent(self, svc):
        assert svc.exists("missing.json") is False
