← [Schema operations](schemas.md) | [Back to README](../README.md) | **Next →** [Dataset operations](datasets.md)

---

# Schema publishers

The two publisher classes handle the full end-to-end flow of publishing a schema to SDS: fetching the file, validating it, posting it via the HTTP service, and reporting any failure. Both are available as public properties on `SdsCommon`.

---

## Publishing a schema from GitHub

Fetches a schema file from the configured GitHub URL, validates it, and posts it to SDS.

```python
from sds_common import SdsCommon

client = SdsCommon()
response = client.github_publisher.publish("068_1.json")
print(response.status_code)  # 200 on success
```

The file is fetched from `GITHUB_SCHEMA_BASE_URL + file_name` using an unauthenticated HTTP client (GitHub raw content is public). See the [configuration reference](configuration.md#all-environment-variables) for `GITHUB_SCHEMA_BASE_URL`.

**Validation checks performed before posting:**

| Check | What it verifies |
|---|---|
| `survey_id` present | The schema JSON contains a `survey_id` field |
| `schema_version` present | The schema JSON contains a `schema_version` field |
| Version matches filename | The `schema_version` value matches the version number in the filename |
| No duplicate | That version does not already exist in SDS |

---

## Publishing a schema from GCS

Reads a schema file from the GCS staging bucket, posts it to SDS, and automatically deletes the staged file on success. If publishing fails for any reason, the file is left in place for inspection or retry.

```python
from sds_common import SdsCommon

client = SdsCommon()
response = client.gcs_publisher.publish("068_1.json")
```

> `gcs_publisher` does **not** run the version duplication check — files in the staging bucket are assumed to have been validated before staging.

> **Failure and ordering:** If `publish()` raises, the staged file is intentionally left in place. If your consumer processes staged files in order (e.g. oldest-first), a persistently failing file will block newer files from being published. Consider routing failed files to a dead-letter location, or alerting on repeated failures, to prevent the queue from stalling.

## Errors

All publisher errors are subclasses of `SchemaPublishError` and include `generate_message_content()`, which serialises the error as JSON — useful for publishing failure events to Pub/Sub.

| Exception | When raised |
|---|---|
| `SchemaFetchError` | GitHub returned a non-200 response when fetching the schema |
| `SchemaJSONDecodeError` | The fetched content could not be parsed as JSON |
| `SurveyIDError` | The schema JSON does not contain a `survey_id` |
| `SchemaVersionError` | The schema JSON does not contain a `schema_version` |
| `SchemaVersionMismatchError` | The version in the JSON does not match the version in the filename |
| `SchemaDuplicationError` | A schema with this version already exists in SDS |
| `SchemaPostError` | SDS returned a non-200 response when posting the schema |
| `FilepathError` | The filepath could not be parsed to extract a filename |

See [Error handling](error_handling.md) for the full exception hierarchy.

---

## Publishing schema errors to Pub/Sub

A common pattern is to catch any publish failure and forward it to a Pub/Sub error topic:

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

See [Pub/Sub messaging](pub_sub.md#publishing-schema-errors-on-failure) for the failure pattern and [Error handling](error_handling.md) for catching specific error types.

---

← [Schema operations](schemas.md) | [Back to README](../README.md) | **Next →** [Dataset operations](datasets.md)
