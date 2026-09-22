"""Tests for bucket_helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

from sds_common.test_helpers.bucket_helpers import delete_blobs_with_test_survey_id


class TestDeleteBlobsWithTestSurveyId:
    def test_deletes_matching_blobs(self):
        bucket = MagicMock()
        blob1 = MagicMock()
        blob2 = MagicMock()
        bucket.list_blobs.return_value = [blob1, blob2]
        delete_blobs_with_test_survey_id(bucket, "test_survey_id")
        bucket.list_blobs.assert_called_once_with(prefix="test_survey_id")
        blob1.delete.assert_called_once()
        blob2.delete.assert_called_once()

    def test_no_blobs_to_delete(self):
        bucket = MagicMock()
        bucket.list_blobs.return_value = []
        delete_blobs_with_test_survey_id(bucket, "test_survey_id")
        bucket.list_blobs.assert_called_once_with(prefix="test_survey_id")
