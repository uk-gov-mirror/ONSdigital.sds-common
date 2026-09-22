from __future__ import annotations
import json
import os

from google.cloud import storage
import logging
from sds_common.interfaces.file_repository_interface import FileRepositoryInterface

logger = logging.getLogger(__name__)


class BucketFileRepository(FileRepositoryInterface):
    def __init__(self, bucket: storage.Bucket):
        self.bucket = bucket

    def get_file_as_json(self, filename: str) -> dict:
        """
        Gets a file from a Google Cloud Bucket with a specific filename and loads it as json.

        :param filename: name of file being loaded.
        :return: dict: the file loaded as json.
        """
        return json.loads(self.bucket.blob(filename).download_as_string())

    def upload_file_from_path(self, filepath: str) -> None:
        """
        Uploads a file to the bucket from a local file path.

        :param filepath: path to the local file to be uploaded.
        """
        filename = os.path.basename(filepath)
        blob = self.bucket.blob(filename)
        blob.upload_from_filename(filepath)

    def delete_file(self, filename: str) -> None:
        """
        Deletes a file from the bucket with the specified filename.

        :param filename: name of the file to be deleted.
        """
        blob = self.bucket.blob(filename)
        blob.delete()

    def check_file_exists(self, filename: str) -> bool:
        """
        Checks if a file exists in the bucket with the specified filename.

        :param filename: name of the file to be checked.
        :return: True if file exists, False otherwise.
        """
        blob = self.bucket.blob(filename)
        return blob.exists()
