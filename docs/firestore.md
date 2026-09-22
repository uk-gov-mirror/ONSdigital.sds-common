← [Dataset operations](datasets.md) | [Back to README](../README.md) | **Next →** [Pub/Sub messaging](pub_sub.md)

---

# Firestore

Access to Firestore is available via `SdsCommon`.

---

## Accessing the schemas collection

```python
from sds_common import SdsCommon

client = SdsCommon()

schemas = client.firestore.get_schemas_collection()

# Stream all documents
for doc in schemas.stream():
    print(doc.id, doc.to_dict())

# Get a specific document
doc = schemas.document("068").get()
if doc.exists:
    print(doc.to_dict())
```

---

← [Dataset operations](datasets.md) | [Back to README](../README.md) | **Next →** [Pub/Sub messaging](pub_sub.md)
