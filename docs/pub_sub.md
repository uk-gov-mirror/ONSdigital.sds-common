← [Firestore](firestore.md) | [Back to README](../README.md) | **Next →** [Error handling](error_handling.md)

---

# Pub/Sub messaging

`client.pub_sub` provides a simple interface for publishing messages to GCP Pub/Sub topics.

---

## Sending a message

```python
from sds_common import SdsCommon

client = SdsCommon()

client.pub_sub.publish(
    message='{"survey_id": "068", "schema_version": "1"}',
    topic_id="my-topic-id",
)
```

Messages must be JSON-encoded strings. The message is published to `projects/{PROJECT_ID}/topics/{topic_id}`.

---

## Using pre-configured topic IDs

The config provides topic IDs for the standard SDS topics so you do not need to hardcode them. See the [configuration reference](configuration.md#all-environment-variables) for all available topic ID variables.

```python
config = client.config

client.pub_sub.publish(
    message=error.generate_message_content(),
    topic_id=config.PUBLISH_SCHEMA_ERROR_TOPIC_ID,
)

client.pub_sub.publish(
    message='{"filepath": "068_1.json"}',
    topic_id=config.PUBLISH_SCHEMA_SUCCESS_TOPIC_ID,
)

client.pub_sub.publish(
    message='{"filepath": "068_1.json"}',
    topic_id=config.PUBLISH_SCHEMA_QUEUE_TOPIC_ID,
)

client.pub_sub.publish(
    message='{"dataset_id": "abc123"}',
    topic_id=config.PUBLISH_DATASET_TOPIC_ID,
)
```

---

## Publishing schema errors on failure

A common pattern is to catch `SchemaPublishError` and publish the error details to the failure topic:

```python
from sds_common import SdsCommon, SchemaPublishError

client = SdsCommon()

try:
    client.github_publisher.publish("068_1.json")
except SchemaPublishError as e:
    client.pub_sub.publish(
        e.generate_message_content(),
        topic_id=client.config.PUBLISH_SCHEMA_ERROR_TOPIC_ID,
    )
    raise
```

`generate_message_content()` returns a JSON string with `error_type`, `message`, and `filepath` fields. See [Error handling](error_handling.md) for the full list of schema exceptions.

---

← [Firestore](firestore.md) | [Back to README](../README.md) | **Next →** [Error handling](error_handling.md)
