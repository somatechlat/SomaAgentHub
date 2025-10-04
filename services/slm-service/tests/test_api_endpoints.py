import math

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_infer_sync_generates_completion():
    response = client.post(
        "/v1/infer/sync",
        json={"prompt": "SomaGent ensures", "max_tokens": 8, "temperature": 0.7},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "somasuite-markov-v1"
    assert isinstance(payload["completion"], str) and payload["completion"]
    usage = payload["usage"]
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
    assert usage["completion_tokens"] == 8


def test_embeddings_endpoint_returns_vectors():
    response = client.post(
        "/v1/embeddings",
        json={"input": ["SomaSuite observability", "no mocks ever"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "somasuite-tfidf-v1"
    vectors = payload["vectors"]
    assert len(vectors) == 2
    assert payload["vector_length"] == len(vectors[0]["embedding"])
    assert payload["vector_length"] > 0
    # ensure embeddings are non-zero and different
    norm_a = math.fsum(x * x for x in vectors[0]["embedding"]) ** 0.5
    norm_b = math.fsum(x * x for x in vectors[1]["embedding"]) ** 0.5
    assert norm_a > 0
    assert norm_b > 0
    assert vectors[0]["embedding"] != vectors[1]["embedding"]
