from __future__ import annotations
from sds_common.interfaces.file_repository_interface import FileRepositoryInterface


class FileService:
    def __init__(self, bucket_repository: FileRepositoryInterface) -> None:
        self.bucket_repository = bucket_repository

    def upload(self, filepath: str) -> None:
        """
        Uploads a file to the associated bucket.

        :param filepath: Path to the file to be uploaded.
        """
        self.bucket_repository.upload_file_from_path(filepath)

    def get_json(self, filename: str) -> dict:
        """
        Retrieves a JSON file from the associated bucket.

        :param filename: Name of the file to be retrieved.
        :return dict: The file loaded as a JSON dictionary.
        """
        return self.bucket_repository.get_file_as_json(filename)

    def delete(self, filename: str) -> None:
        """
        Deletes a file from the associated bucket.

        :param filename: Name of the file to be deleted.
        """
        self.bucket_repository.delete_file(filename)

    def exists(self, filename: str) -> bool:
        """
        Returns True if the file exists in the associated bucket.

        :param filename: Name of the file to be checked.
        :return bool: True if the file exists, False otherwise.
        """
        return self.bucket_repository.check_file_exists(filename)
