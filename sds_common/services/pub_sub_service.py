from __future__ import annotations
from google.cloud.pubsub_v1 import PublisherClient


class PubSubService:
    def __init__(self, publisher_client: PublisherClient, project_id: str) -> None:
        self.publisher = publisher_client
        self.project_id = project_id

    def publish(self, message: str, topic_id: str) -> None:
        """
        Publishes a message to the specified topic.

        :param message: The JSON-encoded string message to publish.
        :param topic_id: The ID of the topic to send the message to.
        """
        topic_path = self.publisher.topic_path(self.project_id, topic_id)
        self.publisher.publish(topic_path, data=message.encode('utf-8'))
