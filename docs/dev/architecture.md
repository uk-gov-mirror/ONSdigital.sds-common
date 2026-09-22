[← Dev README](README.md) | [Back to main README](../../README.md)

---

# Architecture

`sds-common` is structured around a single **facade** class — `SdsCommon` — that acts as the composition root for all services. Nothing is instantiated until it is accessed.

---

## Facade and lazy DI

All services are `@cached_property` on `SdsCommon`. The first access to a property constructs the object (injecting its dependencies from other properties on the same facade) and caches it for the lifetime of the `SdsCommon` instance.

```
SdsCommon
├── config                  @cached_property → Config
├── iap_auth                @cached_property → AuthHeaderProvider(secrets, config)
├── schemas                 @cached_property → SdsSchemaRequestService(authenticated_http, config)
├── datasets                @cached_property → SdsDatasetRequestService(authenticated_http, config)
├── github_publisher        @cached_property → GithubSchemaPublisher(schemas, validator, http, config)
├── gcs_publisher           @cached_property → GcsSchemaPublisher(schemas, schema_staging_files)
├── firestore               @cached_property → FirebaseLoader(firestore_client)
│
├── _secrets                @cached_property → SecretService(config)
├── _http                   @cached_property → HttpService (unauthenticated)
├── _authenticated_http     @property        → HttpService (fresh IAP token each access)
├── _authenticated_session  @cached_property → requests.Session (shared retry adapter)
├── _schema_staging_files   @cached_property → FileService (SCHEMA_PUBLISH_BUCKET)
├── _dataset_files          @cached_property → FileService (DATASET_BUCKET)
├── pub_sub                 @cached_property → PubSubService
├── _schema_validator       @cached_property → SchemaValidatorService(schemas)
└── _firestore_client       @cached_property → firestore.Client
```

**Public** properties (no `_` prefix) are part of the user-facing API and are documented in the user docs.  
**Private** properties (prefixed `_`) are internal wiring — they exist on the facade so their dependencies are resolved in one place but are not intended for direct use by consumers.

---

## Why `_authenticated_http` is a plain `@property`

IAP tokens expire after ~1 hour. If `_authenticated_http` were a `@cached_property`, the same stale token would be reused indefinitely. Making it a plain `@property` constructs a fresh `HttpService` (with a new token) on each access. The underlying `requests.Session` (connection pooling, retry adapter) is still cached separately via `_authenticated_session`.

> **Caution:** Do not cache the object returned by `client._authenticated_http` in your own code. The value is intentionally short-lived — caching it means requests will eventually fail with a 401 when the token expires. Always access it via the facade so the token is refreshed automatically.

---

## Bucket cache

`BucketLoader.fetch_bucket()` caches `google.cloud.storage.Bucket` references in a dictionary keyed by the `Bucket` enum. This means GCS bucket objects are resolved once per `SdsCommon` instance and reused. If a bucket is deleted or permissions are revoked after first access, the stale reference will remain until the `SdsCommon` instance is recreated (e.g. on the next Cloud Function invocation). This is an intentional trade-off — for long-running services experiencing bucket access errors mid-flight, recreating the `SdsCommon` instance resolves the issue.

---

## Directory structure

```
sds_common/
├── config/
│   ├── config.py               # Config dataclass + get_config() singleton
│   └── logging_config.py       # GCP structured JSON logging
├── enums/
│   └── buckets.py              # Bucket enum (SCHEMA_PUBLISH_BUCKET, DATASET_BUCKET)
├── models/
│   ├── auth_errors.py
│   ├── config_errors.py
│   ├── dataset_publish_errors.py
│   ├── schema_publish_errors.py
│   └── storage_errors.py
├── publishers/
│   ├── schema_publisher.py     # Abstract base
│   ├── gcs_schema_publisher.py
│   └── github_schema_publisher.py
├── repositories/
│   ├── bucket_file_repository.py  # GCS CRUD operations
│   └── bucket_loader.py           # Resolves bucket by enum
├── services/
│   ├── auth_header_provider.py
│   ├── file_service.py
│   ├── http_service.py
│   ├── pub_sub_service.py
│   ├── schema_validator_service.py
│   ├── sds_dataset_request_service.py
│   ├── sds_schema_request_service.py
│   └── secret_service.py
├── test_helpers/
│   ├── firebase_loader.py
│   └── pub_sub_helper.py
└── sds_common.py               # Facade / composition root
```

---

## Adding a new feature

1. Create the service class in `sds_common/services/` (or `publishers/` for publish pipelines)
2. Wire it into `SdsCommon` as a `@cached_property`, injecting dependencies from existing properties
3. If it should be user-facing, use a public name (no `_` prefix) and add it to the user docs
4. If it is internal wiring only, prefix it with `_`
5. Write unit tests; aim for 100% coverage
