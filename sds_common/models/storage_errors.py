from __future__ import annotations
class BucketNotFoundError(Exception):
    """Raised when a named GCS bucket cannot be found in Google Cloud Storage."""

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        super().__init__(f"Bucket '{bucket_name}' not found in Google Cloud Storage.")
