# sds-common — Developer guide

This section is for contributors to `sds-common` itself. If you are a **consumer** of the library, see the [main README](../../README.md) and [user docs](../README_DOCS.md) instead.

---

## Contents

| Guide | What it covers |
|---|---|
| [Architecture](architecture.md) | Facade, lazy DI, internal wiring |
| [File storage internals](file_storage.md) | `FileService` and `BucketFileRepository` |
| [Pub/Sub internals](pub_sub.md) | `PubSubService` — internal usage and direct access |
| [Testing](testing.md) | Unit test patterns, mock injection, coverage |

---

## Quick start

```bash
git clone git@github.com:ONSdigital/sds-common.git
cd sds-common
uv sync --all-groups
make test
```

---

## Adding a new public method

1. Add the method to the relevant service class under `sds_common/services/` or `sds_common/publishers/`
2. If the service needs to be publicly exposed, add a `@cached_property` to `SdsCommon` in `sds_common/sds_common.py`
3. Write tests in the matching `tests/` subdirectory
4. Document it in the relevant user-facing doc under `docs/`

See [Architecture](architecture.md) for how the facade wires dependencies together.
