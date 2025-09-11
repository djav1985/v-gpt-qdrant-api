import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.embeddings import router as embeddings_router
from app.dependencies import get_embeddings_model
from app.models import EmbeddingResponse
from app.config import get_settings


class DummyModel:
    def embed(self, text: str):
        return np.array([0.1, 0.2])


def create_client():
    get_settings.cache_clear()
    app = FastAPI()
    app.include_router(embeddings_router)
    app.dependency_overrides[get_embeddings_model] = lambda: DummyModel()
    import app.routes.embeddings as emb_module
    emb_module.get_embeddings_model = lambda: DummyModel()
    return TestClient(app)


def _headers(key: str = "test"):
    return {"X-API-Key": key}


def test_embedding_endpoint(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    client = create_client()
    resp = client.post("/embeddings", json={"text": "hello"}, headers=_headers("secret"))
    assert resp.status_code == 200
    EmbeddingResponse.model_validate(resp.json())
    assert resp.json()["embedding"] == [0.1, 0.2]
