# Migration guide: v1 → v2

Version 2.0.0 is a significant rewrite of `sds-common`. The public API, configuration, and exception hierarchy have all changed. This guide covers every breaking change and the steps needed to update consuming code.

---

## Overview of breaking changes

| Area | What changed |
|---|---|
| Entry point | A new `SdsCommon` facade replaces direct service instantiation |
| `Config` | No longer a class with module-level attributes — must be instantiated |
| Environment variables | Several keys renamed (see [below](#environment-variable-renames)) |
| `HttpService` | No longer owns auth logic; use `schemas` or `datasets` from `SdsCommon` — they are pre-wired with authenticated HTTP |
| `AuthHeaderProvider` | New class — extracted from `HttpService` |
| Facade properties | Clean noun-based names (see [below](#facade-property-names)) |
| Service methods | Intent-based names (see [below](#service-method-names)) |
| Exception hierarchy | Exceptions reorganised into typed, domain-specific files |
| `schemas.get_metadata()` | Now returns `list[dict] \| None` instead of a raw `Response` object |
| `datasets.get_metadata()` | Now returns `list[DatasetMetadata] \| None` (404 → `None`); previously raised on 404 |
| `pub_sub.publish()` | Renamed from `send_message()`; no longer accepts a `SchemaPublishError` |
| Dependencies removed | `cloudevents`, `pydantic_settings`, `python-dotenv` removed from package deps |

---

## 1. Replace direct service instantiation with `SdsCommon`

In v1, services were constructed manually, often at module level. In v2, use the `SdsCommon` facade. Services are lazily initialised — only what you access is created.

**Before (v1):**
```python
from sds_common.config.config import Config
from sds_common.services.http_service import HttpService
from sds_common.services.sds_schema_request_service import SdsSchemaRequestService

config = Config
http = HttpService(authenticated=True)
schema_service = SdsSchemaRequestService(http_service=http, config=config)
metadata = schema_service.get_schema_metadata("068")
```

**After (v2):**
```python
from sds_common import SdsCommon

client = SdsCommon()
metadata = client.schemas.get_metadata("068")
```

---

## 2. `Config` is now an instance, not a class

In v1, `Config` was a class with class-level attributes read at import time. In v2, `Config` must be instantiated and reads from the environment at construction time.

**Before (v1):**
```python
from sds_common.config.config import Config

project_id = Config.PROJECT_ID  # class attribute access
```

**After (v2):**
```python
from sds_common import get_config, CONFIG

# Option A — cached singleton
project_id = get_config().PROJECT_ID

# Option B — lazy proxy (backward-compatible module-level usage)
from sds_common import CONFIG
project_id = CONFIG.PROJECT_ID  # identical behaviour, defers until first access
```

---

## 3. Environment variable renames

The following environment variables have been renamed. Update Cloud Run, Cloud Functions, Kubernetes, and any `.env` files accordingly.

| v1 name | v2 name |
|---|---|
| `LOADER_URL` | `SDS_LOADER_URL` |
| `PROCESS_TIMEOUT` | `HTTP_REQUEST_TIMEOUT_SECONDS` |
| `SECRET_ID` | `IAP_SECRET_ID` |
| `GITHUB_SCHEMA_URL` | `GITHUB_SCHEMA_BASE_URL` |
| `POST_SCHEMA_URL` | `POST_SCHEMA_PATH` |
| `GET_SCHEMA_METADATA_URL` | `GET_SCHEMA_METADATA_PATH` |
| `GET_ALL_SCHEMA_METADATA_URL` | `GET_ALL_SCHEMA_METADATA_PATH` |
| `GET_DATASET_METADATA_URL` | `GET_DATASET_METADATA_PATH` |
| `SCHEMA_PUBLISH_BUCKET_NAME` | `SCHEMA_STAGING_BUCKET_NAME` |

All other variable names are unchanged.

In addition, the **default values** for the endpoint path variables have been updated from the deprecated `/v1/` paths to the current SDS API paths:

| Variable | v1 default (deprecated) | v2 default |
|---|---|---|
| `POST_SCHEMA_PATH` | `/v1/schema` | `/schemas` |
| `GET_SCHEMA_METADATA_PATH` | `/v1/schema_metadata` | `/schemas/metadata` |
| `GET_ALL_SCHEMA_METADATA_PATH` | `/v1/all_schema_metadata` | `/schemas/all-metadata` |
| `GET_DATASET_METADATA_PATH` | `/v1/dataset_metadata` | `/datasets/metadata` |

If your deployment explicitly set these variables to `/v1/...` values, update them or remove the overrides to use the new defaults.

---

## 4. `HttpService` no longer owns authentication

In v1, `HttpService` accepted a boolean `authenticated` flag. In v2, it is a pure HTTP client. Authenticated requests go through `client.schemas` and `client.datasets` — these are pre-wired with an authenticated HTTP client internally.

**Before (v1):**
```python
from sds_common.services.http_service import HttpService

http = HttpService(authenticated=True)
response = http.make_get_request("https://sds.example.com/api")

unauth_http = HttpService(authenticated=False)
response = unauth_http.make_get_request("https://raw.githubusercontent.com/...")
```

**After (v2):**
```python
from sds_common import SdsCommon

client = SdsCommon()

# Authenticated (IAP Bearer token injected automatically)
# Use the pre-wired services instead:
metadata = client.schemas.get_metadata("068")
# or
metadata = client.datasets.get_metadata("068", "202301")

# Unauthenticated (e.g. GitHub)
response = client.http.make_get_request("https://raw.githubusercontent.com/...")
```

If you need an `HttpService` directly (outside of `SdsCommon`), use the factory:

```python
from sds_common import HttpService

http = HttpService.create()                        # unauthenticated
http = HttpService.create(headers=my_headers)     # with custom headers
```

---

## 5. Generating authentication headers

In v1, auth header generation was tied to `HttpService`. In v2, use `AuthHeaderProvider` directly or via `SdsCommon`.

**Before (v1):**
```python
from sds_common.services.http_service import HttpService

http = HttpService(authenticated=True)
# headers were set internally — not accessible directly
```

**After (v2):**
```python
from sds_common import SdsCommon

client = SdsCommon()

# Metadata server (for GCP-hosted services)
headers = client.iap_auth.generate()

# IAM impersonation (for local development)
headers = client.iap_auth.generate_by_impersonation()
```

Or if you only need headers without the full facade:

```python
from sds_common import AuthHeaderProvider, SecretService, get_config

config = get_config()
provider = AuthHeaderProvider(secret_service=SecretService(config=config), config=config)
headers = provider.generate()
```

---

## 6. `schemas.get_metadata()` return type changed

In v1, `get_schema_metadata` returned a raw `requests.Response` object. In v2, the method is `get_metadata()` and returns `list[dict] | None`.

**Before (v1):**
```python
response = schema_service.get_schema_metadata("068")
data = response.json()  # manually decode
```

**After (v2):**
```python
metadata = client.schemas.get_metadata("068")

if metadata is None:
    # survey does not exist (404)
    ...
else:
    for entry in metadata:
        print(entry)  # already a dict
```

---

## 7. `pub_sub.publish()` replaces `send_message()`

In v1, `send_message` accepted a `SchemaPublishError` object. In v2, the method is `publish()` and accepts a plain `str` (JSON-encoded message) and a `topic_id`.

**Before (v1):**
```python
pub_sub_service.send_message(error, topic_id="my-topic")  # v1: error object passed directly
```

**After (v2):**
```python
client.pub_sub.publish(error.generate_message_content(), topic_id="my-topic")
```

`generate_message_content()` is available on all `SchemaPublishError` subclasses and returns a JSON string.

---

## 8. Facade property names

`SdsCommon` uses clean, noun-based property names rather than `_service` suffixes.

| v2 name |
|---|
| `secrets` |
| `http` |
| `schemas`, `datasets` |
| `schemas` |
| `datasets` |
| `schema_staging_files` |
| `dataset_files` |
| `pub_sub` |

---

## 9. Service method names

Methods are named for their intent, not their HTTP verb or implementation detail.

| Class | Method |
|---|---|
| `SdsSchemaRequestService` | `get_metadata(survey_id)` |
| `SdsSchemaRequestService` | `get_all_metadata()` |
| `SdsSchemaRequestService` | `publish(schema)` |
| `SdsDatasetRequestService` | `get_metadata(survey_id, period_id)` |
| `SchemaValidatorService` | `validate(schema)` |
| `GcsSchemaPublisher` | `publish(file_name)` |
| `GithubSchemaPublisher` | `publish(file_name)` |
| `PubSubService` | `publish(message, topic_id)` |
| `FileService` | `upload(filepath)` |
| `FileService` | `get_json(filename)` |
| `FileService` | `delete(filename)` |
| `FileService` | `exists(filename)` |

---

## 10. Exception imports have moved

Exceptions are now organised into domain-specific modules. All are still importable from the package root (`from sds_common import ...`), but direct module imports will need updating.

| Exception | v1 module | v2 module |
|---|---|---|
| `SecretAccessError` | `sds_common.models.schema_publish_errors` | `sds_common.models.auth_errors` |
| `SecretKeyError` | `sds_common.models.schema_publish_errors` | `sds_common.models.auth_errors` |
| `BucketNotFoundError` | `sds_common.repositories.bucket_loader` | `sds_common.models.storage_errors` |
| `EnvironmentVariableError` | (inline, not exported) | `sds_common.models.config_errors` |
| `SchemaMetadataFormatError` | (did not exist) | `sds_common.models.schema_publish_errors` |

**Recommended:** import all exceptions from the package root to be insulated from future reorganisation:

```python
from sds_common import (
    SdsAuthError,
    SecretAccessError,
    SecretKeyError,
    SchemaPublishError,
    SchemaFetchError,
    BucketNotFoundError,
    EnvironmentVariableError,
)
```

---

## 11. Removed/changed dependencies

The following packages are no longer installed as transitive dependencies of `sds-common`. If your project relied on them being pulled in transitively, add them to your own `pyproject.toml`:

- `cloudevents`
- `pydantic_settings`
- `python-dotenv`
- `firebase-admin` (replaced internally by `google-cloud-firestore` directly)

`google-cloud-iam` is now an **optional** dependency rather than a hard requirement. It is only needed for `iap_auth.generate_by_impersonation()` (local development). Install it explicitly if you use that method:

```bash
uv add "sds-common[impersonation]" --index https://<ARTIFACT_REGISTRY_URL>/simple/
# or
uv add sds-common[impersonation]
```

---

## 12. Test isolation — config cache

If you use `get_config()` in tests, the `@lru_cache` will cause the same `Config` instance to be reused across tests. Add this fixture to your `conftest.py`:

```python
import pytest
from sds_common.config.config import get_config

@pytest.fixture(autouse=True)
def clear_config_cache():
    get_config.cache_clear()
    yield
    get_config.cache_clear()
```

---

## Quick reference — new import paths

```python
from sds_common import SdsCommon              # main entry point
from sds_common import get_config, CONFIG     # config access
from sds_common import Bucket                 # GCS bucket enum
from sds_common import DatasetMetadata        # data class returned by datasets.get_metadata()
from sds_common import PubSubHelper           # integration test helper

# Errors
from sds_common import (
    SdsAuthError, SecretAccessError, SecretKeyError,
    SchemaPublishError, SchemaFetchError, SchemaPostError,
    SchemaMetadataError, SchemaMetadataFormatError,
    SchemaDuplicationError, SchemaVersionError, SchemaVersionMismatchError,
    SurveyIDError, SchemaJSONDecodeError, FilepathError,
    DatasetPublishError, DatasetMetadataRetrievalError, DatasetCreateError,
    BucketNotFoundError, EnvironmentVariableError,
)
```
