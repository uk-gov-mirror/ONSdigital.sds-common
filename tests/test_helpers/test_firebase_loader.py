"""Tests for FirebaseLoader."""
from __future__ import annotations

from unittest.mock import MagicMock

from sds_common.test_helpers.firebase_loader import FirebaseLoader


class TestFirebaseLoader:
    def _make_loader(self):
        client = MagicMock()
        schemas_collection = MagicMock()
        client.collection.return_value = schemas_collection
        loader = FirebaseLoader(client=client)
        return loader, client, schemas_collection

    def test_get_client_returns_client(self):
        loader, client, _ = self._make_loader()
        assert loader.get_client() is client

    def test_get_schemas_collection_returns_collection(self):
        loader, client, schemas_collection = self._make_loader()
        result = loader.get_schemas_collection()
        assert result is schemas_collection
        client.collection.assert_called_once_with("schemas")

    def test_schemas_collection_set_on_init(self):
        loader, client, _ = self._make_loader()
        client.collection.assert_called_once_with("schemas")
