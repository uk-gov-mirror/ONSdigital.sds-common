# sds-common

`sds-common` is a Python library that provides a single, easy-to-use client for interacting with the Supplementary Data Service (SDS) and common GCP infrastructure. It handles authentication, schema publishing, dataset retrieval, file storage, Pub/Sub messaging, and Firestore access — all behind a single facade class that lazily initialises only what you need.

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [The `SdsCommon` facade](#the-sdscommon-facade)
- [Documentation by topic](#documentation-by-topic)
- [Migrating from v1](MIGRATION.md)

---

## Installation

`sds-common` is hosted on a private GCP Artifact Registry and is not available on PyPI.

```bash
uv add sds-common --index https://<ARTIFACT_REGISTRY_URL>/simple/
```

Or with pip:

```bash
pip install sds-common --index-url https://<ARTIFACT_REGISTRY_URL>/simple/
```

The optional IAM impersonation extra is needed for local development authentication:

```bash
uv add "sds-common[impersonation]" --index https://<ARTIFACT_REGISTRY_URL>/simple/
```

See [Authentication → Strategy 2 (local development)](docs/authentication.md#strategy-2--iam-impersonation-local-development) for when this is needed.

---

## Quick start

```python
from sds_common import SdsCommon

client = SdsCommon()

# Fetch schema metadata for a survey
metadata = client.schemas.get_metadata("068")

# Publish a schema from GitHub to SDS
response = client.github_publisher.publish("068_1.json")

# Upload a file to the schema GCS bucket

# Send a Pub/Sub message
client.pub_sub.publish('{"event": "schema_published"}', topic_id="my-topic")
```

Nothing is initialised until first access. If you only need auth headers, only the secret manager and IAP auth provider are created — no GCS clients, no Firestore connections, nothing else.

---

## Configuration

The library is configured entirely through environment variables. Most variables have sensible defaults for the `ons-sds-sandbox` project, but `SDS_URL` and `SDS_LOADER_URL` are required.

| Environment variable | Default | Description |
|---|---|---|
| `PROJECT_ID` | `ons-sds-sandbox` | GCP project ID |
| `SDS_URL` | **required** | Base URL of the SDS API |
| `SDS_LOADER_URL` | **required** | Base URL of the loader service |
| `HTTP_REQUEST_TIMEOUT_SECONDS` | `540` | HTTP request timeout in seconds |
| `IAP_SECRET_ID` | `iap-secret` | GCP Secret Manager secret ID for the IAP OAuth credential |
| `GITHUB_SCHEMA_BASE_URL` | `https://raw.githubusercontent.com/ONSdigital/sds-schema-definitions/main/` | Base URL for raw schema files on GitHub |
| `POST_SCHEMA_PATH` | `/schemas` | SDS endpoint for posting a new schema |
| `GET_SCHEMA_METADATA_PATH` | `/schemas/metadata` | SDS endpoint for fetching schema metadata for a survey |
| `GET_ALL_SCHEMA_METADATA_PATH` | `/schemas/all-metadata` | SDS endpoint for fetching all schema metadata |
| `GET_DATASET_METADATA_PATH` | `/datasets/metadata` | SDS endpoint for fetching dataset metadata for a survey and period |
| `DATASET_CREATE_PATH` | `/events/dataset/create` | SDS endpoint for creating a dataset |
| `DATASET_DELETE_PATH` | `/events/dataset/delete` | SDS endpoint for deleting a dataset |
| `PUBLISH_SCHEMA_ERROR_TOPIC_ID` | `ons-sds-publish-schema-fail` | Pub/Sub topic for schema publish failures |
| `PUBLISH_SCHEMA_SUCCESS_TOPIC_ID` | `ons-sds-publish-schema` | Pub/Sub topic for schema publish successes |
| `PUBLISH_SCHEMA_QUEUE_TOPIC_ID` | `schema-publish-queue` | Pub/Sub topic for the schema publish queue |
| `PUBLISH_DATASET_TOPIC_ID` | `ons-sds-publish-dataset` | Pub/Sub topic for dataset publishing |
| `FIRESTORE_DB_NAME` | `{PROJECT_ID}-sds` | Firestore database name |
| `SCHEMA_STAGING_BUCKET_NAME` | `{PROJECT_ID}-sds-europe-west2-schema-publish` | GCS bucket for schemas awaiting publishing |
| `DATASET_BUCKET_NAME` | `{PROJECT_ID}-sds-europe-west2-dataset` | GCS bucket for datasets |
| `LOG_LEVEL` | `INFO` | Log level for GCP structured logging (see [Logging for GCP](docs/configuration.md#logging-for-gcp-cloud-logging)) |

---

## The `SdsCommon` facade

`SdsCommon` is the single entry point for the library. Instantiate it once; every property is lazily created on first access and then cached for the lifetime of the instance.

```python
from sds_common import SdsCommon

client = SdsCommon()
```

You can also supply a pre-built `Config` instance, which is useful in tests:

```python
from sds_common import SdsCommon, Config

client = SdsCommon(config=my_config)
```

### Available properties

| Property | Type | Description |
|---|---|---|
| `config` | `Config` | Resolved configuration object — see [Configuration reference](docs/configuration.md) |
| `iap_auth` | `AuthHeaderProvider` | Generates IAP auth headers — see [Authentication](docs/authentication.md) |
| `schemas` | `SdsSchemaRequestService` | HTTP calls to SDS schema endpoints — see [Schema operations](docs/schemas.md) |
| `datasets` | `SdsDatasetRequestService` | HTTP calls to SDS dataset endpoints — see [Dataset operations](docs/datasets.md) |
| `gcs_publisher` | `GcsSchemaPublisher` | Publishes schemas from the GCS staging bucket to SDS — see [Schema publishers](docs/publishers.md#publishing-a-schema-from-gcs) |
| `github_publisher` | `GithubSchemaPublisher` | Fetches schemas from GitHub, validates, and publishes to SDS — see [Schema publishers](docs/publishers.md#publishing-a-schema-from-github) |
| `firestore` | `FirebaseLoader` | Typed Firestore wrapper for schema collection access — see [Firestore](docs/firestore.md) |
| `pub_sub` | `PubSubService` | Publishes messages to GCP Pub/Sub topics — see [Pub/Sub messaging](docs/pub_sub.md) |

---

## Documentation by topic

Read these in order for a complete tour, or jump directly to what you need:

| Guide | What it covers |
|---|---|
| [Authentication](docs/authentication.md) | Generating IAP headers, metadata server vs impersonation, secret format |
| [Schema operations](docs/schemas.md) | Fetching metadata, posting schemas directly to SDS |
| [Schema publishers](docs/publishers.md) | Publishing schemas from GitHub or GCS with validation |
| [Dataset operations](docs/datasets.md) | Fetching dataset metadata |
| [Firestore](docs/firestore.md) | Accessing the Firestore database and schema collection |
| [Pub/Sub messaging](docs/pub_sub.md) | Publishing messages to Pub/Sub topics |
| [Error handling](docs/error_handling.md) | Full exception hierarchy and how to catch specific errors |
| [Testing helpers](docs/testing_helpers.md) | `PubSubHelper` for integration tests; unit test patterns |
| [Configuration reference](docs/configuration.md) | All environment variables, overriding config in tests, GCP logging |
| [Developer guide](docs/dev/README.md) | Architecture, internals, contributing |


