import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.embeddings import embeddings_router
from dependencies import get_embeddings_model


class DummyModel:
    def embed(self, text: str):
        return np.array([0.1, 0.2])


def create_client():
    app = FastAPI()
    app.include_router(embeddings_router)
    app.dependency_overrides[get_embeddings_model] = lambda: DummyModel()
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
    assert resp.json()["embedding"] == [0.1, 0.2]
