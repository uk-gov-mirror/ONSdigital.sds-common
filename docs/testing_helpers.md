← [Error handling](error_handling.md) | [Back to README](../README.md) | **Next →** [Configuration reference](configuration.md)

---

# Testing helpers

`sds-common` includes `PubSubHelper` for integration tests that need to interact with real GCP Pub/Sub infrastructure.

---

## `PubSubHelper`

`PubSubHelper` manages the lifecycle of a Pub/Sub subscriber in a test, and provides methods to read and assert on messages published during the test.

### Setup

```python
from google.cloud import pubsub_v1
from sds_common import PubSubHelper

helper = PubSubHelper(
    topic_id="my-topic",
    subscriber_client=pubsub_v1.SubscriberClient(),
    publisher_client=pubsub_v1.PublisherClient(),
    project_id="my-gcp-project",
)
```

### Typical integration test pattern

```python
SUBSCRIBER_ID = "my-test-subscriber"

# Before the test: create the subscriber and drain any leftover messages
helper.try_create_subscriber(SUBSCRIBER_ID)
helper.purge_messages(SUBSCRIBER_ID)

# Run the action under test
trigger_some_schema_publish()

# Assert on the messages produced
messages = helper.pull_and_acknowledge_messages(SUBSCRIBER_ID)
assert messages is not None
assert messages[0]["survey_id"] == "068"

# After the test: clean up
helper.try_delete_subscriber(SUBSCRIBER_ID)
```

### Method reference

| Method | Description |
|---|---|
| `try_create_subscriber(subscriber_id)` | Creates the subscription if it does not exist; polls until confirmed active. Raises `RuntimeError` if it cannot be confirmed after retries. |
| `try_delete_subscriber(subscriber_id)` | Deletes the subscription if it exists; polls until confirmed gone. Raises `RuntimeError` if it cannot be confirmed deleted after retries. |
| `publish_message(message)` | Publishes a raw string message to the topic. |
| `pull_and_acknowledge_messages(subscriber_id)` | Pulls up to 5 messages, acknowledges them, and returns them as `list[dict]`. Returns `None` if no messages were available. |
| `purge_messages(subscriber_id)` | Seeks the subscription to a far-future timestamp, discarding all pending messages. |
| `format_received_message_data(received_message)` | Decodes a raw Pub/Sub message into a `dict`. |

### Notes

- `try_create_subscriber` is idempotent — skips creation if the subscription already exists.
- Retry loops use exponential backoff starting at 0.5 s with 5 attempts.

---

## Writing unit tests for code that uses `sds-common`

### Clearing the config cache between tests

`get_config()` is cached with `@lru_cache`. Patch environment variables in unit tests and always clear the cache to prevent cross-test pollution. See the [configuration reference](configuration.md#overriding-config-in-tests) for other config override options.

```python
import pytest
from sds_common import get_config

@pytest.fixture(autouse=True)
def clear_config_cache():
    get_config.cache_clear()
    yield
    get_config.cache_clear()
```

### Injecting mocks into the facade

`SdsCommon` properties are `@cached_property`. Inject mocks directly into the instance's `__dict__` to bypass the descriptor:

```python
from unittest.mock import MagicMock
from sds_common import SdsCommon

def test_something():
    client = SdsCommon()
    client.__dict__["schemas"] = MagicMock()

    # client.schemas now returns the mock
```

---

← [Error handling](error_handling.md) | [Back to README](../README.md) | **Next →** [Configuration reference](configuration.md)
