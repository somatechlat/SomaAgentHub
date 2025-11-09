import os
import sys

from fastapi.testclient import TestClient

BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.main import app  # type: ignore  # noqa: E402

client = TestClient(app)


def test_create_snapshot_create_only(monkeypatch):
    # Fake ClickHouse client storing snapshot in memory

    store = {}

    class FakeCH:
        def execute(self, query, params=None, with_column_types=False, types_check=False):  # noqa: D401
            nonlocal store
            q = " ".join(query.split()).lower()
            if q.startswith("insert into pricing_snapshots"):
                row = params[0]
                sid = row[0]
                store[str(sid)] = {"header": row, "offers": []}
                return []
            if q.startswith("insert into pricing_snapshot_offers"):
                # append offers
                sid = None
                for r in params:
                    sid = r[0]
                    store[str(sid)]["offers"].append(r)
                return []
            if q.startswith("select snapshot_id") and "from pricing_snapshots" in q:
                sid = params["sid"]
                row = store.get(str(sid), {}).get("header")
                if not row:
                    return ([], []) if with_column_types else []
                # emulate column order expected by main.get_snapshot
                data = [row]
                cols = [
                    ("snapshot_id", "UUID"),
                    ("created_at", "DateTime"),
                    ("offer_count", "UInt32"),
                    ("min_price_hour", "Float32"),
                    ("median_price_hour", "Float32"),
                    ("p95_price_hour", "Float32"),
                    ("hash_fixed", "String"),
                ]
                return (data, cols) if with_column_types else data
            if q.startswith("select id,") and "from pricing_snapshot_offers" in q:
                sid = params["sid"]
                offers = store.get(str(sid), {}).get("offers", [])
                return offers
            return []

    # Patch get_client
    import app.main as pricing_main  # noqa: E402

    monkeypatch.setattr(pricing_main, "get_client", lambda: FakeCH())

    # create snapshot
    r = client.post("/v1/pricing/snapshot")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "snapshot_id" in data


def test_budget_with_policy_soft_no_opa():
    # Without OPA running, endpoint should still return a decision payload
    r = client.post(
        "/v1/pricing/evaluate-budget/with-policy",
        params={
            "gpu_model": "A100",
            "hours_planned": 1.0,
            "quantity": 1,
            "budget_cap": 50,
        },
    )
    assert r.status_code == 200
    payload = r.json()
    assert "estimated_cost" in payload
    # policy_decision may be null due to no OPA
    assert "policy_decision" in payload
