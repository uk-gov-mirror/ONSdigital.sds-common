from __future__ import annotations
import json
import time
from typing import Any

from google.api_core.exceptions import GoogleAPIError, NotFound
from google.cloud import pubsub_v1

import logging

logger = logging.getLogger(__name__)


class PubSubHelper:
    def __init__(
        self,
        topic_id: str,
        subscriber_client: pubsub_v1.SubscriberClient,
        publisher_client: pubsub_v1.PublisherClient,
        project_id: str,
    ) -> None:
        self.subscriber_client = subscriber_client
        self.publisher_client = publisher_client
        self.topic_id = topic_id
        self.project_id = project_id

    def try_create_subscriber(self, subscriber_id: str) -> None:
        """
        Creates a subscriber with a unique subscriber id if one does not already exist,
        then polls until the subscription is confirmed active.

        :param subscriber_id: the unique id of the subscriber being created.
        :raises RuntimeError: if the subscription cannot be confirmed after all retry attempts.
        """
        topic_path = self.publisher_client.topic_path(self.project_id, self.topic_id)
        subscription_path = self.subscriber_client.subscription_path(self.project_id, subscriber_id)

        if not self._subscription_exists(subscriber_id):
            self.subscriber_client.create_subscription(
                request={
                    'name': subscription_path,
                    'topic': topic_path,
                    'enable_message_ordering': True,
                }
            )

        created = self._wait_and_check_subscription_exists(subscriber_id)
        if not created:
            raise RuntimeError(
                f'Failed to create subscriber. Subscription path: {subscription_path}'
            )
        # _wait_and_check returns True on success

    def publish_message(self, message: str) -> None:
        """
        Publishes a message to a topic.

        :param message: the message to be published.
        """
        topic_path = self.publisher_client.topic_path(self.project_id, self.topic_id)
        self.publisher_client.publish(topic_path, data=message.encode('utf-8'))

    def pull_and_acknowledge_messages(self, subscriber_id: str) -> list[dict] | None:
        """
        Pulls all messages published to a topic via a subscriber.

        :param subscriber_id: the unique id of the subscriber being created.
        :return list[dict] | None: The list of formatted messages received from the topic,
            or None if no messages were received.
        """
        subscription_path = self.subscriber_client.subscription_path(self.project_id, subscriber_id)
        response = self.subscriber_client.pull(
            request={'subscription': subscription_path, 'max_messages': 5},
        )

        if len(response.received_messages) == 0:
            return None

        messages = []
        ack_ids = []

        for received_message in response.received_messages:
            messages.append(self.format_received_message_data(received_message))
            ack_ids.append(received_message.ack_id)

        self.subscriber_client.acknowledge(
            request={'subscription': subscription_path, 'ack_ids': ack_ids}
        )

        return messages

    def purge_messages(self, subscriber_id: str) -> None:
        """
        Purges all messages published to a subscriber by seeking through future timestamp.

        :param subscriber_id: the unique id of the subscriber being created.
        """
        subscription_path = self.subscriber_client.subscription_path(self.project_id, subscriber_id)
        self.subscriber_client.seek(
            request={'subscription': subscription_path, 'time': '2999-01-01T00:00:00Z'}
        )

    def format_received_message_data(self, received_message: Any) -> dict:
        """
        Formats a messages received from a topic.

        :param received_message: The message received from the topic.
        :return dict: The formatted message data.
        """
        return json.loads(received_message.message.data.decode('utf-8').replace("'", '"'))

    def try_delete_subscriber(self, subscriber_id: str) -> None:
        """
        Deletes a subscriber if it exists, then polls until the deletion is confirmed.

        :param subscriber_id: the unique id of the subscriber being deleted.
        :raises RuntimeError: if the subscription cannot be confirmed deleted after all retry attempts.
        """
        subscription_path = self.subscriber_client.subscription_path(self.project_id, subscriber_id)

        if self._subscription_exists(subscriber_id):
            self.subscriber_client.delete_subscription(
                request={'subscription': subscription_path}
            )

        if not self._wait_and_check_subscription_deleted(subscriber_id):
            raise RuntimeError(
                f'Failed to delete subscriber. Subscription path: {subscription_path}'
            )

    def _subscription_exists(self, subscriber_id: str) -> bool:
        """
        Checks a subscription exists.

        :param subscriber_id: the unique id of the subscriber being checked.
        :return bool: True if the subscription exists, False otherwise.
        """
        subscription_path = self.subscriber_client.subscription_path(self.project_id, subscriber_id)

        try:
            self.subscriber_client.get_subscription(request={'subscription': subscription_path})
            return True
        except NotFound:
            return False
        except GoogleAPIError:
            raise
        except Exception:
            logger.warning(
                'Unexpected error checking subscription existence for %s',
                subscription_path,
                exc_info=True,
            )
            return False

    def _wait_and_check_subscription_exists(
        self,
        subscriber_id: str,
        attempts: int = 5,
        backoff: float = 0.5,
    ) -> bool:
        """
        Waits for a subscription to be created and checks if it exists.

        :param subscriber_id: the unique id of the subscriber being checked.
        :param attempts: the number of attempts to check if the subscription exists.
        :param backoff: the time in seconds to wait between attempts.
        :return bool: True if the subscription exists, False otherwise.
        """
        while attempts != 0:
            if self._subscription_exists(subscriber_id):
                return True

            attempts -= 1
            time.sleep(backoff)
            backoff += backoff

        return False

    def _wait_and_check_subscription_deleted(
        self,
        subscriber_id: str,
        attempts: int = 5,
        backoff: float = 0.5,
    ) -> bool:
        """
        Waits for a subscription to be deleted and checks if it is gone.

        :param subscriber_id: the unique id of the subscriber being checked.
        :param attempts: the number of attempts to check if the subscription is deleted.
        :param backoff: the time in seconds to wait between attempts.
        :return bool: True if the subscription is deleted, False otherwise.
        """
        while attempts != 0:
            if not self._subscription_exists(subscriber_id):
                return True

            attempts -= 1
            time.sleep(backoff)
            backoff += backoff

        return False
