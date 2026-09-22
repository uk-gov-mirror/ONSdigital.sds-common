"""Tests for firestore_helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

from sds_common.test_helpers.firestore_helpers import (
    _delete_document,
    _delete_sub_collection_in_batches,
    perform_delete_on_collection_with_test_survey_id,
)


class TestDeleteSubCollectionInBatches:
    def test_deletes_docs_in_batch(self):
        client = MagicMock()
        batch = MagicMock()
        client.batch.return_value = batch

        doc1 = MagicMock()
        doc2 = MagicMock()
        sub_collection_ref = MagicMock()
        sub_collection_ref.limit.return_value.get.return_value = [doc1, doc2]

        count = _delete_sub_collection_in_batches(client, sub_collection_ref, 10)
        assert count == 2
        batch.commit.assert_called_once()

    def test_returns_zero_for_empty_collection(self):
        client = MagicMock()
        batch = MagicMock()
        client.batch.return_value = batch
        sub_ref = MagicMock()
        sub_ref.limit.return_value.get.return_value = []
        count = _delete_sub_collection_in_batches(client, sub_ref, 10)
        assert count == 0


class TestDeleteDocument:
    def test_deletes_document_with_no_subcollections(self):
        client = MagicMock()
        doc_ref = MagicMock()
        doc_ref.collections.return_value = []
        result = _delete_document(client, doc_ref)
        assert result is True
        doc_ref.delete.assert_called_once()

    def test_deletes_subcollection_documents_before_parent(self):
        client = MagicMock()
        batch = MagicMock()
        client.batch.return_value = batch

        sub_collection = MagicMock()
        # Return 0 docs so the while loop exits immediately
        sub_collection.limit.return_value.get.return_value = []

        doc_ref = MagicMock()
        doc_ref.collections.return_value = [sub_collection]

        _delete_document(client, doc_ref)
        doc_ref.delete.assert_called_once()


class TestPerformDeleteOnCollectionWithTestSurveyId:
    def test_deletes_matching_documents(self):
        client = MagicMock()
        batch = MagicMock()
        client.batch.return_value = batch

        doc1 = MagicMock()
        doc1.reference.collections.return_value = []

        collection_ref = MagicMock()
        collection_ref.where.return_value.where.return_value.stream.return_value = [doc1]

        perform_delete_on_collection_with_test_survey_id(client, collection_ref, "test_survey_id")
        doc1.reference.delete.assert_called_once()

    def test_no_matching_documents(self):
        client = MagicMock()
        collection_ref = MagicMock()
        collection_ref.where.return_value.where.return_value.stream.return_value = []
        perform_delete_on_collection_with_test_survey_id(client, collection_ref, "test_survey_id")
