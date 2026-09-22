[← Dev README](README.md) | [Back to main README](../../README.md)

---

# File storage internals

`FileService` wraps `BucketFileRepository` to provide file operations on a specific GCS bucket. Three instances are wired into `SdsCommon` as private properties.

---

## Available file services

| Facade property | Bucket | Config variable |
|---|---|---|
| `_schema_staging_files` | Schemas awaiting publishing | `SCHEMA_STAGING_BUCKET_NAME` |
| `_dataset_files` | Datasets | `DATASET_BUCKET_NAME` |

These are used internally by `GcsSchemaPublisher` and related services. They are not exposed publicly.

---

## `FileService` methods

| Method | Description |
|---|---|
| `upload(local_path)` | Uploads a local file; uses the local filename as the GCS object name |
| `get_json(filename)` | Downloads a file and deserialises it as a Python `dict` |
| `exists(filename)` | Returns `True` if the object exists in the bucket |
| `delete(filename)` | Deletes the object from the bucket |

---

## `BucketFileRepository`

`FileService` delegates all GCS operations to `BucketFileRepository`, which holds the `google.cloud.storage.Bucket` instance. The repository is constructed by `BucketLoader`, which resolves the correct bucket name from `Config` using the `Bucket` enum.

```
Bucket enum → BucketLoader → google.cloud.storage.Bucket → BucketFileRepository → FileService
```

---

## Errors

`BucketNotFoundError` is raised by `BucketLoader.fetch_bucket()` if the bucket named in config does not exist. This surfaces when a `FileService` property is first accessed on the facade (i.e. when a publisher or other service first uses file storage).

See [Error handling](../error_handling.md#bucketnotfounderror) for details.
