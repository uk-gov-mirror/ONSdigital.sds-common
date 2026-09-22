from __future__ import annotations
def delete_blobs_with_test_survey_id(bucket, test_survey_id: str):
    """
    Deletes all blobs with the given survey ID prefix from the specified bucket.

    :param bucket: the bucket to clean
    :param test_survey_id: the test survey id
    """
    blobs = bucket.list_blobs(prefix=test_survey_id)

    for blob in blobs:
        blob.delete()
