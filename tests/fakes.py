"""Fake implementations of repository interfaces for use in tests."""
from __future__ import annotations

import json
import os

from sds_common.interfaces.file_repository_interface import FileRepositoryInterface


class FakeBucketFileRepository(FileRepositoryInterface):
    """
    In-memory fake implementation of FileRepositoryInterface.

    Stores files as a dict[filename -> dict]. Use this in tests instead of
    MagicMock when you want to assert on actual state (file exists, content
    is correct) rather than on call signatures.
    """

    def __init__(self, initial_files: dict[str, dict] | None = None) -> None:
        self._store: dict[str, dict] = initial_files or {}

    def get_file_as_json(self, filename: str) -> dict:
        if filename not in self._store:
            raise FileNotFoundError(f"File not found in fake bucket: {filename}")
        return self._store[filename]

    def upload_file_from_path(self, filepath: str) -> None:
        filename = os.path.basename(filepath)
        with open(filepath) as f:
            self._store[filename] = json.load(f)

    def delete_file(self, filename: str) -> None:
        self._store.pop(filename, None)

    def check_file_exists(self, filename: str) -> bool:
        return filename in self._store

    def add(self, filename: str, content: dict) -> None:
        """Seed the fake with a file for test setup."""
        self._store[filename] = content

    @property
    def files(self) -> dict[str, dict]:
        """Read-only view of stored files — use for assertions."""
        return dict(self._store)
