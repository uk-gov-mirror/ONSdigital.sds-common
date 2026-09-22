[← Dev README](README.md) | [Back to main README](../../README.md)

---

# Testing

---

## Running the tests

```bash
make test
```

Or directly:

```bash
uv run --only-group test pytest --cov=sds_common --cov-report=term-missing
```

The suite targets 100% coverage. CI enforces this via the `unit-tests` workflow.

---

## Test structure

```
tests/
├── test_sds_common.py                          # Facade / SdsCommon
├── test_logging_config.py                      # GCP structured logging
├── test_services/
│   ├── test_auth_header_provider.py
│   ├── test_file_service.py
│   ├── test_http_service.py
│   ├── test_pub_sub_service.py
│   ├── test_schema_validator_service.py
│   ├── test_sds_dataset_request_service.py
│   ├── test_sds_schema_request_service.py
│   └── test_secret_service.py
├── test_repositories/
│   └── test_bucket_file_repository.py
├── test_publishers/
│   ├── test_gcs_schema_publisher.py
│   └── test_github_schema_publisher.py
├── test_config/
│   └── test_config.py
├── test_errors/
│   └── test_errors.py
└── test_helpers/
    └── test_pub_sub_helper.py
```

---

## Mock injection patterns

### `@cached_property` — inject via `__dict__`

```python
from unittest.mock import MagicMock
from sds_common import SdsCommon

def test_something():
    client = SdsCommon()
    client.__dict__["schemas"] = MagicMock()
    # client.schemas now returns the mock without constructing the real service
```

This works for any `@cached_property` (both public and private `_`-prefixed ones).

### `@property` — inject its dependency instead

`_authenticated_http` is a plain `@property` (not cached) so `__dict__` injection is not possible. Inject `iap_auth` instead, since `_authenticated_http` calls `self.iap_auth.generate()` internally:

```python
from unittest.mock import MagicMock
from sds_common import SdsCommon

def test_authenticated_http():
    client = SdsCommon()
    mock_auth = MagicMock()
    mock_auth.generate.return_value = {"Authorization": "******"}
    client.__dict__["iap_auth"] = mock_auth
    client.__dict__["_authenticated_session"] = MagicMock()

    http = client._authenticated_http
    # http is constructed with the mock session and headers
```

---

## Config isolation between tests

`get_config()` is cached with `@lru_cache`. Always clear the cache before and after tests that patch environment variables:

```python
import pytest
from sds_common import get_config

@pytest.fixture(autouse=True)
def clear_config_cache():
    get_config.cache_clear()
    yield
    get_config.cache_clear()
```
