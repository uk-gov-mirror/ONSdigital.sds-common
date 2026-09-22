from __future__ import annotations
import time

from sds_common.test_helpers.common_test_data import test_survey_id
from sds_common.test_helpers.firebase_loader import FirebaseLoader
from sds_common.test_helpers.firestore_helpers import perform_delete_on_collection_with_test_survey_id
from sds_common.test_helpers.pub_sub_helper import PubSubHelper


def cleanup(firebase_loader: FirebaseLoader):
    """
    Cleans up all schema test data created in buckets/FireStore.
    Should be run before and after test to account for test failures.
    """
    client = firebase_loader.get_client()
    perform_delete_on_collection_with_test_survey_id(
        client,
        firebase_loader.get_schemas_collection(),
        test_survey_id,
    )


def pubsub_setup(pubsub_helper: PubSubHelper, subscriber_id: str):
    """Creates any subscribers that may be used in tests"""
    pubsub_helper.try_create_subscriber(subscriber_id)


def pubsub_teardown(pubsub_helper: PubSubHelper, subscriber_id: str):
    """Deletes subscribers that may have been used in tests"""
    pubsub_helper.try_delete_subscriber(subscriber_id)


def pubsub_purge_messages(pubsub_helper: PubSubHelper, subscriber_id: str):
    """Purge any messages that may have been sent to a subscriber"""
    pubsub_helper.purge_messages(subscriber_id)


def inject_wait_time(seconds: int):
    """
    Injects a wait time to allow GCP resources to spin up and tear down.

    :param seconds: the number of seconds to wait
    """
    time.sleep(seconds)


def poll_subscription(pubsub_helper: PubSubHelper, subscriber_id: str, timeout: int = 45) -> list[dict] | None:
    """
    Polls a subscription for messages until the timeout is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = pubsub_helper.pull_and_acknowledge_messages(subscriber_id)
        if response:
            return response
        time.sleep(3)
    return None
