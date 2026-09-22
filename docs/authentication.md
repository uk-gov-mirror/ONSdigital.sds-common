← [Back to README](../README.md) | **Next →** [Schema operations](schemas.md)

---

# Authentication

SDS endpoints are protected by Google Cloud IAP (Identity-Aware Proxy). `sds-common` handles all authentication automatically — you never manage tokens yourself.

---

## How it works

Every request to an IAP-secured endpoint needs an `Authorization: Bearer <token>` header. The token is a short-lived OpenID Connect ID token (~1 hour) issued for a specific OAuth client ID, which is stored in GCP Secret Manager and read at runtime.

When you access any authenticated service through the facade, a fresh token is generated automatically.

---

## Making authenticated requests

```python
from sds_common import SdsCommon

client = SdsCommon()

# Use any SDS service — authentication is handled automatically
metadata = client.schemas.get_metadata("068")
datasets = client.datasets.get_metadata("068", "202301")
```

---

## Generating headers explicitly

If you need the raw headers (e.g. to pass to a third-party HTTP client):

```python
from sds_common import SdsCommon

client = SdsCommon()

# Strategy 1: GCP metadata server — use when running inside GCP
# (Cloud Run, Cloud Functions, GCE, etc.)
headers = client.iap_auth.generate()

# Strategy 2: IAM impersonation — use for local development
headers = client.iap_auth.generate_by_impersonation()
```

Both return: `{"Authorization": "Bearer <token>", "Content-Type": "application/json"}`

---

## Strategy 1 — Metadata server (GCP-hosted)

Used automatically for Cloud Run, Cloud Functions, GCE and similar. No local credentials required — the GCP metadata server is called directly.

---

## Strategy 2 — IAM impersonation (local development)

Impersonates the App Engine default service account via IAM.

**Requirements:**
- Application Default Credentials (ADC) configured: `gcloud auth application-default login`
- Your ADC account must hold the `Service Account Token Creator` IAM role on `{PROJECT_ID}@appspot.gserviceaccount.com`
- `google-cloud-iam` installed: `uv add "sds-common[impersonation]" --index https://<ARTIFACT_REGISTRY_URL>/simple/`

---

## Secret format

The IAP OAuth client ID is read from GCP Secret Manager. The secret must be a JSON object structured as:

```json
{
  "web": {
    "client_id": "your-oauth-client-id.apps.googleusercontent.com"
  }
}
```

The secret name is configured via `IAP_SECRET_ID` (default: `iap-secret`). See the [configuration reference](configuration.md#all-environment-variables) for all available options.

---

## Errors

| Exception | When raised |
|---|---|
| `SecretAccessError` | GCP Secret Manager is unreachable or returns an error |
| `SecretKeyError` | The `web.client_id` key is missing from the secret payload |

```python
from sds_common import SdsCommon, SecretAccessError, SecretKeyError

client = SdsCommon()
try:
    headers = client.iap_auth.generate()
except SecretAccessError as e:
    print(f"Could not read secret: {e.error_detail}")
except SecretKeyError:
    print("Secret payload is missing the OAuth client ID key")
```

---

← [Back to README](../README.md) | **Next →** [Schema operations](schemas.md)
