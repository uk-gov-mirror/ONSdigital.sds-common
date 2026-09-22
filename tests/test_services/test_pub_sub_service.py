"""Tests for PubSubService."""
from __future__ import annotations

from sds_common.services.pub_sub_service import PubSubService


import pytest


@pytest.fixture
def service(mock_publisher_client) -> PubSubService:
    return PubSubService(publisher_client=mock_publisher_client, project_id="proj")


class TestPubSubService:
    def test_send_message_publishes_to_correct_topic(self, service, mock_publisher_client):
        service.publish('{"error_type": "E", "message": "M", "filepath": "/f"}', "my-topic")
        mock_publisher_client.topic_path.assert_called_once_with("proj", "my-topic")
        mock_publisher_client.publish.assert_called_once()

    def test_send_message_encodes_as_utf8_bytes(self, service, mock_publisher_client):
        service.publish('{"key": "value"}', "my-topic")
        call_args = mock_publisher_client.publish.call_args
        published_data = call_args[1].get("data") or call_args[0][1]
        assert isinstance(published_data, bytes)
        assert b'"key"' in published_data

    def test_send_message_uses_project_id(self, service, mock_publisher_client):
        service.publish("msg", "topic-id")
        mock_publisher_client.topic_path.assert_called_with("proj", "topic-id")

    def test_send_message_accepts_plain_string(self, service, mock_publisher_client):
        """PubSubService is decoupled from SchemaPublishError — accepts any str."""
        service.publish("plain string message", "topic-id")
        mock_publisher_client.publish.assert_called_once()

    def test_schema_publish_error_can_be_serialised_for_send_message(self, service, mock_publisher_client):
        """Callers serialise errors themselves before passing to send_message."""
        from sds_common.models.schema_publish_errors import SchemaPublishError
        error = SchemaPublishError("EType", "A message", "/path.json")
        service.publish(error.generate_message_content(), "my-topic")
        mock_publisher_client.publish.assert_called_once()
