# somagent-somabrain

Async Python client for SomaBrain’s HTTP API. Thin wrapper used by SomaGent services (memory gateway, constitution service, benchmark harness).

## Usage

```python
from somagent_somabrain import SomaBrainClient, RememberPayload

client = SomaBrainClient(base_url="http://localhost:9696")
payload = RememberPayload(text="Pay ACME invoice on Friday", tags=["todo"])

await client.remember("demo", payload)
```
```
