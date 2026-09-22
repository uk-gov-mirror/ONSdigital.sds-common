[← Dev README](README.md) | [Back to main README](../../README.md)

---

# Pub/Sub internals

`PubSubService` wraps the GCP `PublisherClient` and is wired into `SdsCommon` as the private `pub_sub` property. It is used internally by services and publishers — it is not part of the public API.

---

## How it is used internally

`pub_sub` is called by error-handling code (outside `sds-common`) and is also the mechanism used in the schema publish failure pattern. For example, callers catching `SchemaPublishError` can publish the error detail to a topic:

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
```

---

## `PubSubService.publish()`

```python
pub_sub.publish(message: str, topic_id: str) -> None
```

Publishes a UTF-8 encoded message to `projects/{PROJECT_ID}/topics/{topic_id}`.

---

## Pre-configured topic IDs

All standard SDS topic IDs are available from `client.config`:

| Config attribute | Purpose |
|---|---|
| `PUBLISH_SCHEMA_ERROR_TOPIC_ID` | Schema publish failure events |
| `PUBLISH_SCHEMA_SUCCESS_TOPIC_ID` | Schema publish success events |
| `PUBLISH_SCHEMA_QUEUE_TOPIC_ID` | Enqueue a schema for publishing |
| `PUBLISH_DATASET_TOPIC_ID` | Dataset events |

See the [configuration reference](../configuration.md#all-environment-variables) for the environment variable names and defaults.
