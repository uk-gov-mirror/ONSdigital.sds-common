from __future__ import annotations
from abc import ABC, abstractmethod


class FileRepositoryInterface(ABC):
    @abstractmethod
    def get_file_as_json(self, filename: str) -> dict:
        """
        Gets a file with a specific filename and loads it as json.

        :param filename: name of file being loaded.
        :return: dict: the file loaded as json.
        """
        ...  # pragma: no cover

    @abstractmethod
    def upload_file_from_path(self, filepath: str) -> None:
        """
        Uploads a file from a local file path.

        :param filepath: path to the local file to be uploaded.
        """
        ...  # pragma: no cover

    @abstractmethod
    def delete_file(self, filename: str) -> None:
        """
        Deletes a file with the specified filename.

        :param filename: name of the file to be deleted.
        """
        ...  # pragma: no cover

    @abstractmethod
    def check_file_exists(self, filename: str) -> bool:
        """
        Checks if a file exists with the specified filename.

        :param filename: name of the file to be checked.
        :return: True if file exists, False otherwise.
        """
        ...  # pragma: no cover
