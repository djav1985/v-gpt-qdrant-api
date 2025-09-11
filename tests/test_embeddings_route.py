import numpy as np
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from routes.embeddings import router as embeddings_router, rate_limiter as emb_rl
from dependencies import get_embeddings_model
from models import EmbeddingResponse


class DummyModel:
    def embed(self, text: str):
        return np.array([0.1, 0.2])


def create_client():
    app = FastAPI()
    app.include_router(embeddings_router)
    app.dependency_overrides[get_embeddings_model] = lambda: DummyModel()

    async def dummy_rate_limiter(request: Request, response: Response):
        response.headers["X-RateLimit-Limit"] = "5"
        response.headers["X-RateLimit-Remaining"] = "4"
        response.headers["X-RateLimit-Reset"] = "1"

    app.dependency_overrides[emb_rl] = dummy_rate_limiter
    import routes.embeddings as emb_module
    emb_module.get_embeddings_model = lambda: DummyModel()

    return TestClient(app)


def _headers(key: str = "test"):
    return {"X-API-Key": key}


def test_embedding_endpoint(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    client = create_client()
    resp = client.post(
        "/embeddings", json={"text": "hello"}, headers=_headers("secret")
    )
    assert resp.status_code == 200
    EmbeddingResponse.model_validate(resp.json())
    for header in [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ]:
        assert header in resp.headers
    assert resp.json()["embedding"] == [0.1, 0.2]
