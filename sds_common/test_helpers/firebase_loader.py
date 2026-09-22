from __future__ import annotations
from google.cloud import firestore


class FirebaseLoader:
    def __init__(self, client: firestore.Client) -> None:
        self.client = client
        self.schemas_collection = self._set_collection('schemas')

    def get_client(self) -> firestore.Client:
        """
        Get the firestore client

        :return: Firestore client
        """
        return self.client

    def get_schemas_collection(self) -> firestore.CollectionReference:
        """
        Get the schemas collection from firestore

        :return: Firestore collection reference for schemas
        """
        return self.schemas_collection

    def _set_collection(self, collection) -> firestore.CollectionReference:
        """
        Setup the collection reference for schemas and datasets

        :param collection: The collection name
        :return: Firestore collection reference
        """
        return self.client.collection(collection)
