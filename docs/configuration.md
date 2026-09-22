← [Testing helpers](testing_helpers.md) | [Back to README](../README.md)

---

# Configuration reference

All configuration is read from environment variables at the time `Config` is first instantiated. Most variables have defaults; `SDS_URL` and `SDS_LOADER_URL` are required.

---

## How configuration works

`Config` is an instance class — not module-level globals. This means nothing is read from the environment until you actually create a `Config` object (or call `SdsCommon()`). This is intentional: it avoids surprising import-time failures and makes the library safe to import in any context.

```python
# Config is not read at import time
from sds_common import SdsCommon

# Config is read here, on first access
client = SdsCommon()
print(client.config.PROJECT_ID)
```

---

## `get_config()` and the `CONFIG` proxy

```python
from sds_common import get_config, CONFIG

# get_config() returns a cached singleton Config instance
config = get_config()

# CONFIG is a lazy proxy — identical to get_config() but usable
# as a module-level constant in legacy code
print(CONFIG.PROJECT_ID)
```

`get_config()` is cached with `@lru_cache(maxsize=1)`. The same `Config` instance is returned on every call within a process.

---

## All environment variables

| Variable | Default | Description |
|---|---|---|
| `PROJECT_ID` | `ons-sds-sandbox` | GCP project ID used for all GCP client connections |
| `SDS_URL` | **required** | Base URL of the SDS API (no trailing slash). Raises `EnvironmentVariableError` if not set. |
| `SDS_LOADER_URL` | **required** | Base URL of the loader service. Raises `EnvironmentVariableError` if not set. |
| `HTTP_REQUEST_TIMEOUT_SECONDS` | `540` | HTTP request timeout in seconds |
| `IAP_SECRET_ID` | `iap-secret` | GCP Secret Manager secret name containing the IAP OAuth credentials |
| `GITHUB_SCHEMA_BASE_URL` | `https://raw.githubusercontent.com/ONSdigital/sds-schema-definitions/main/` | Base URL for fetching schema files from GitHub |
| `POST_SCHEMA_PATH` | `/schemas` | SDS path for `POST /schemas` — posts a schema for processing |
| `GET_SCHEMA_METADATA_PATH` | `/schemas/metadata` | SDS path for `GET /schemas/metadata` — fetch metadata for a survey |
| `GET_ALL_SCHEMA_METADATA_PATH` | `/schemas/all-metadata` | SDS path for `GET /schemas/all-metadata` — fetch all schema metadata |
| `GET_DATASET_METADATA_PATH` | `/datasets/metadata` | SDS path for `GET /datasets/metadata` — fetch dataset metadata for a survey and period |
| `DATASET_CREATE_PATH` | `/events/dataset/create` | SDS path for the dataset create event |
| `DATASET_DELETE_PATH` | `/events/dataset/delete` | SDS path for the dataset delete event |
| `PUBLISH_SCHEMA_ERROR_TOPIC_ID` | `ons-sds-publish-schema-fail` | Pub/Sub topic ID for schema publish failure events |
| `PUBLISH_SCHEMA_SUCCESS_TOPIC_ID` | `ons-sds-publish-schema` | Pub/Sub topic ID for schema publish success events |
| `PUBLISH_SCHEMA_QUEUE_TOPIC_ID` | `schema-publish-queue` | Pub/Sub topic ID for the schema publish queue |
| `PUBLISH_DATASET_TOPIC_ID` | `ons-sds-publish-dataset` | Pub/Sub topic ID for dataset events |
| `FIRESTORE_DB_NAME` | `{PROJECT_ID}-sds` | Firestore database name |
| `SCHEMA_STAGING_BUCKET_NAME` | `{PROJECT_ID}-sds-europe-west2-schema-publish` | GCS bucket for schemas staged for publishing |
| `DATASET_BUCKET_NAME` | `{PROJECT_ID}-sds-europe-west2-dataset` | GCS bucket for dataset files |
| `LOG_LEVEL` | `INFO` | Log level for GCP structured logging (see [Logging for GCP](#logging-for-gcp-cloud-logging)) |

---

## Overriding config in tests

> See also: [Testing helpers → Clearing the config cache](testing_helpers.md#clearing-the-config-cache-between-tests) and [Testing helpers → Injecting mocks](testing_helpers.md#injecting-mocks-into-the-facade) for the full testing guide.

### Option 1 — Patch environment variables

```python
import pytest
from unittest.mock import patch
from sds_common.config.config import get_config

@pytest.fixture(autouse=True)
def clear_config_cache():
    get_config.cache_clear()
    yield
    get_config.cache_clear()

def test_something(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "my-test-project")
    monkeypatch.setenv("SDS_URL", "https://test.sds.example.com")

    config = get_config()
    assert config.PROJECT_ID == "my-test-project"
```

> **Important:** Always call `get_config.cache_clear()` before and after each test to prevent the cached singleton leaking between tests.

### Option 2 — Pass a `Config` directly to `SdsCommon`

```python
from sds_common import SdsCommon, Config
from unittest.mock import MagicMock, patch

with patch.dict("os.environ", {"PROJECT_ID": "test-project", "SDS_URL": "http://localhost"}):
    config = Config()

client = SdsCommon(config=config)
```

### Option 3 — Mock the config object

```python
from unittest.mock import MagicMock
from sds_common import SdsCommon

mock_config = MagicMock()
mock_config.PROJECT_ID = "test-project"
mock_config.SDS_URL = "http://localhost"

client = SdsCommon(config=mock_config)
```

---

## Logging for GCP (Cloud Logging)

`sds-common` automatically configures GCP-structured JSON logging when it is imported, provided no logging handlers have been set up yet. For most applications — Cloud Run services, Cloud Functions, GKE workloads — **no setup is required**. Just import `sds-common` and all logs from both `sds-common` and your own code will be structured JSON that GCP Cloud Logging parses natively.

> **Note:** This is a deliberate import-time side effect. If you are using `sds-common` as a dependency in a larger application that manages its own logging configuration, set up your handlers **before** importing `sds-common` — the auto-configuration only runs when no handlers are present, so your setup will not be touched.

### What you get out of the box

All log output is emitted as single-line JSON with fields that GCP understands:

```json
{"severity": "WARNING", "message": "Failed to post schema. Status code: 500", "logger": "sds_common.services.sds_schema_request_service", "stackTrace": "..."}
```

| Field | Present when | Description |
|---|---|---|
| `severity` | Always | GCP log level — parsed natively for filtering and alerting |
| `message` | Always | The log message |
| `logger` | Always | The Python logger name (e.g. module path) |
| `stackTrace` | `WARNING` and above | Full call stack at the point the log was emitted — always captured automatically so you always know where warnings/errors originated |
| `traceback` | Exception is active | Full exception traceback, e.g. when using `logger.exception()` or logging inside an `except` block |

### If your app already configures logging

If your application sets up its own logging handlers before importing `sds-common`, the auto-configuration is skipped and your setup is left untouched. `sds-common` only runs its default configuration when no handlers are present.

### Overriding the log level

The log level defaults to the `LOG_LEVEL` environment variable (or `INFO` if not set). To override it explicitly:

```python
import logging
from sds_common import configure_gcp_logging

configure_gcp_logging(level=logging.DEBUG)
```

This replaces whatever handlers are currently configured, so call it early in your startup code.

### Using the formatter directly

If you need more control (e.g. attaching the formatter to a specific handler or logger):

```python
import logging
from sds_common import GcpJsonFormatter

handler = logging.StreamHandler()
handler.setFormatter(GcpJsonFormatter())
logging.getLogger("my.logger").addHandler(handler)
```

---

← [Testing helpers](testing_helpers.md) | [Back to README](../README.md)
