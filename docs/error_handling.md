← [Pub/Sub messaging](pub_sub.md) | [Back to README](../README.md) | **Next →** [Testing helpers](testing_helpers.md)

---

# Error handling

All exceptions raised by `sds-common` are importable directly from the package root and fit into a clear hierarchy so you can catch at the right level of specificity.

---

## Exception hierarchy

```
Exception
├── SdsAuthError                     # auth_errors.py
│   ├── SecretAccessError
│   └── SecretKeyError
│
├── SchemaPublishError               # schema_publish_errors.py
│   ├── FilepathError
│   ├── SchemaDuplicationError
│   ├── SchemaVersionMismatchError
│   ├── SurveyIDError
│   ├── SchemaVersionError
│   ├── SchemaJSONDecodeError
│   ├── SchemaFetchError
│   ├── SchemaPostError
│   ├── SchemaMetadataError
│   └── SchemaMetadataFormatError
│
├── DatasetPublishError              # dataset_publish_errors.py
│   ├── DatasetMetadataRetrievalError
│   └── DatasetCreateError
│
├── BucketNotFoundError              # storage_errors.py
│
└── EnvironmentVariableError         # config_errors.py
```

---

## Catching errors

### Catch a specific error

```python
from sds_common import SdsCommon, SchemaFetchError, SchemaDuplicationError

client = SdsCommon()

try:
    client.github_publisher.publish("068_1.json")
except SchemaFetchError as e:
    print(f"Could not fetch schema from GitHub: {e.message}")
except SchemaDuplicationError as e:
    print(f"Schema already exists: {e.message}")
```

### Catch all schema publish errors

```python
from sds_common import SdsCommon, SchemaPublishError

client = SdsCommon()

try:
    client.github_publisher.publish("068_1.json")
except SchemaPublishError as e:
    # generate_message_content() returns a JSON string suitable for Pub/Sub
    # See: Schema publishers → Publishing schema errors to Pub/Sub
    print(e.generate_message_content())
```

### Catch authentication errors

```python
from sds_common import SdsCommon, SdsAuthError, SecretAccessError

client = SdsCommon()

try:
    headers = client.iap_auth.generate()
except SecretAccessError as e:
    print(f"Secret Manager error: {e.error_detail}")
except SdsAuthError:
    print("Authentication failed")
```

See [Authentication](authentication.md) for full context on how IAP authentication works.

---

## Error reference

### `SdsAuthError` (base)
Base class for all authentication and secret-management errors. Subclass of `Exception`.

### `SecretAccessError`
Raised when GCP Secret Manager cannot be reached or returns an API error.
- Attribute: `error_detail: str` — the underlying GCP error message.

### `SecretKeyError`
Raised when the retrieved secret payload does not contain the expected `web.client_id` key.

---

### `SchemaPublishError` (base)
Base class for all schema-related errors. All subclasses share:
- `error_type: str` — machine-readable error category
- `message: str` — human-readable description
- `filepath: str` — path to the schema file that caused the error (or `"N/A"`)
- `generate_message_content() -> str` — serialises the error as a JSON string

### `FilepathError`
The schema filepath could not be split to extract a filename.

### `SchemaDuplicationError`
A schema with the same version already exists in SDS.

### `SchemaVersionMismatchError`
The `schema_version` in the JSON body does not match the version number in the filename.

### `SurveyIDError`
The schema JSON does not contain a `survey_id`.

### `SchemaVersionError`
The schema JSON does not contain a `schema_version`.

### `SchemaJSONDecodeError`
The raw content downloaded from GitHub (or GCS) could not be parsed as JSON.

### `SchemaFetchError`
GitHub returned a non-200 HTTP status when fetching the schema.
- `status_code` is included in the message.

### `SchemaPostError`
SDS returned a non-200 HTTP status when posting the schema.
- `status_code` is included in the message.

### `SchemaMetadataError`
SDS returned a non-200/404 status when requesting schema metadata.

### `SchemaMetadataFormatError`
The schema metadata response body was not a list — indicates an unexpected API contract change.
- Attribute: `survey_id: str`

---

### `DatasetPublishError` (base)
Base class for all dataset-related errors.

### `DatasetMetadataRetrievalError`
SDS returned a non-200 response for a dataset metadata request.
- Attribute: `message: str`

### `DatasetCreateError`
SDS returned a non-200 response when creating a dataset.
- Attribute: `message: str`

---

### `BucketNotFoundError`
The named GCS bucket does not exist.
- Attribute: `bucket_name: str`

---

### `EnvironmentVariableError`
A required environment variable was not set and has no default.
- Attribute: `variable_name: str`

---

← [Pub/Sub messaging](pub_sub.md) | [Back to README](../README.md) | **Next →** [Testing helpers](testing_helpers.md)
