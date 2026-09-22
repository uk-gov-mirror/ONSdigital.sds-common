← [Authentication](authentication.md) | [Back to README](../README.md) | **Next →** [Schema publishers](publishers.md)

---

# Schema operations

These operations call the SDS HTTP API directly via `client.schemas`.

---

## Fetching schema metadata

### For a specific survey

```python
from sds_common import SdsCommon

client = SdsCommon()

# Returns a list of metadata dicts, or None if the survey does not exist
metadata = client.schemas.get_metadata("068")

if metadata is None:
    print("No schemas found for this survey")
else:
    for entry in metadata:
        print(entry)
```

### All schemas

```python
all_metadata = client.schemas.get_all_metadata()
# Returns a list of all schema metadata dicts
```

---

## Posting a schema directly

```python
response = client.schemas.publish(schema_dict, filepath="068_1.json")
print(response.status_code)  # 200 on success
```

`filepath` is optional — it is only used in error messages if the post fails. This posts the schema JSON directly to SDS with no prior validation. For the full publish pipeline (fetch → validate → post), use [`github_publisher`](publishers.md#publishing-a-schema-from-github) or [`gcs_publisher`](publishers.md#publishing-a-schema-from-gcs).

---

## Errors

| Exception | When raised |
|---|---|
| `SchemaMetadataError` | SDS returned a non-200/404 response for a metadata request |
| `SchemaMetadataFormatError` | The metadata response body was not in the expected list format |
| `SchemaPostError` | SDS returned a non-200 response when posting the schema |

See [Error handling](error_handling.md) for the full exception hierarchy.

---

← [Authentication](authentication.md) | [Back to README](../README.md) | **Next →** [Schema publishers](publishers.md)
