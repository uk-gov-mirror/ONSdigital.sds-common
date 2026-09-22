"""Tests for PubSubHelper."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import NotFound

from sds_common.test_helpers.pub_sub_helper import PubSubHelper


def _make_helper(topic_id="my-topic"):
    subscriber_client = MagicMock()
    publisher_client = MagicMock()
    publisher_client.topic_path.return_value = "projects/proj/topics/my-topic"
    subscriber_client.subscription_path.return_value = "projects/proj/subscriptions/sub-id"
    helper = PubSubHelper(
        topic_id=topic_id,
        subscriber_client=subscriber_client,
        publisher_client=publisher_client,
        project_id="proj",
    )
    return helper, subscriber_client, publisher_client


class TestPubSubHelper:
    def test_publish_message(self):
        helper, _, publisher = _make_helper()
        helper.publish_message("hello")
        publisher.publish.assert_called_once()
        args = publisher.publish.call_args
        assert args[1].get("data") == b"hello" or args[0][1] == b"hello"

    def test_pull_and_acknowledge_messages_returns_none_when_empty(self):
        helper, subscriber, _ = _make_helper()
        response = MagicMock()
        response.received_messages = []
        subscriber.pull.return_value = response
        result = helper.pull_and_acknowledge_messages("sub-id")
        assert result is None

    def test_pull_and_acknowledge_messages_returns_messages(self):
        helper, subscriber, _ = _make_helper()
        msg = MagicMock()
        msg.message.data = json.dumps({"key": "value"}).encode()
        msg.ack_id = "ack1"
        response = MagicMock()
        response.received_messages = [msg]
        subscriber.pull.return_value = response
        result = helper.pull_and_acknowledge_messages("sub-id")
        assert result is not None
        assert len(result) == 1
        subscriber.acknowledge.assert_called_once()

    def test_format_received_message_data(self):
        helper, _, _ = _make_helper()
        msg = MagicMock()
        msg.message.data = json.dumps({"a": 1}).encode()
        assert helper.format_received_message_data(msg) == {"a": 1}

    def test_purge_messages_calls_seek(self):
        helper, subscriber, _ = _make_helper()
        helper.purge_messages("sub-id")
        subscriber.seek.assert_called_once()

    def test_subscription_exists_returns_true(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.return_value = MagicMock()
        assert helper._subscription_exists("sub-id") is True

    def test_subscription_exists_returns_false_on_google_api_error(self):
        from google.api_core.exceptions import NotFound
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = NotFound("not found")
        assert helper._subscription_exists("sub-id") is False

    def test_subscription_exists_returns_false_and_logs_on_unexpected_exception(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = RuntimeError("connection reset")
        with patch("sds_common.test_helpers.pub_sub_helper.logger") as mock_logger:
            result = helper._subscription_exists("sub-id")
        assert result is False
        mock_logger.warning.assert_called_once()
        # exc_info=True must be passed so the traceback appears in logs
        _, kwargs = mock_logger.warning.call_args
        assert kwargs.get("exc_info") is True

    def test_try_create_subscriber_skips_create_if_already_exists(self):
        helper, subscriber, _ = _make_helper()
        # Subscription already exists — confirmed immediately
        subscriber.get_subscription.return_value = MagicMock()
        helper.try_create_subscriber("sub-id")
        subscriber.create_subscription.assert_not_called()

    def test_try_delete_subscriber_skips_delete_if_not_exists(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = NotFound("not found")
        helper.try_delete_subscriber("sub-id")
        subscriber.delete_subscription.assert_not_called()


class TestPubSubHelperRetryLoops:
    """Cover retry/polling branches."""

    def test_try_create_subscriber_creates_when_not_exists(self):
        helper, subscriber, _ = _make_helper()
        # First call: doesn't exist → create; second call: exists (polling confirms)
        subscriber.get_subscription.side_effect = [NotFound("not found"), MagicMock()]
        helper.try_create_subscriber("sub-id")
        subscriber.create_subscription.assert_called_once()

    def test_try_create_subscriber_raises_on_exhausted_retries(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = NotFound("not found")
        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="Failed to create subscriber"):
                helper.try_create_subscriber("sub-id")

    def test_try_delete_subscriber_deletes_when_exists(self):
        helper, subscriber, _ = _make_helper()
        # First call: exists → delete; second call (polling): gone
        subscriber.get_subscription.side_effect = [MagicMock(), Exception("not found")]
        helper.try_delete_subscriber("sub-id")
        subscriber.delete_subscription.assert_called_once()

    def test_try_delete_subscriber_raises_on_exhausted_retries(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.return_value = MagicMock()  # always exists
        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="Failed to delete subscriber"):
                helper.try_delete_subscriber("sub-id")

    def test_wait_and_check_subscription_exists_retries_then_succeeds(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = [NotFound("not found"), MagicMock()]
        with patch("time.sleep"):
            assert helper._wait_and_check_subscription_exists("sub-id", attempts=2, backoff=0) is True

    def test_wait_and_check_subscription_exists_returns_false_when_exhausted(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = NotFound("not found")
        with patch("time.sleep"):
            assert helper._wait_and_check_subscription_exists("sub-id", attempts=2, backoff=0) is False

    def test_wait_and_check_subscription_deleted_retries_then_succeeds(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.side_effect = [MagicMock(), Exception("not found")]
        with patch("time.sleep"):
            assert helper._wait_and_check_subscription_deleted("sub-id", attempts=2, backoff=0) is True

    def test_wait_and_check_subscription_deleted_returns_false_when_exhausted(self):
        helper, subscriber, _ = _make_helper()
        subscriber.get_subscription.return_value = MagicMock()
        with patch("time.sleep"):
            assert helper._wait_and_check_subscription_deleted("sub-id", attempts=2, backoff=0) is False
