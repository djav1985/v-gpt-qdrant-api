import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.memory import memory_router
from dependencies import create_qdrant_client, get_embeddings_model


class DummyModel:
    def embed(self, text: str):
        return np.array([0.1, 0.2, 0.3])


def create_client():
    mock_qdrant = Mock()
    mock_qdrant.upsert = AsyncMock()
    mock_qdrant.search = AsyncMock()
    mock_qdrant.create_collection = AsyncMock()
    mock_qdrant.create_payload_index = AsyncMock()
    mock_qdrant.delete_collection = AsyncMock()
    mock_qdrant.delete = AsyncMock()

    app = FastAPI()
    app.include_router(memory_router)
    app.dependency_overrides[create_qdrant_client] = lambda: mock_qdrant
    app.dependency_overrides[get_embeddings_model] = lambda: DummyModel()
    # Patch direct calls within route module
    import routes.memory as memory_module
    memory_module.get_embeddings_model = lambda: DummyModel()
    client = TestClient(app)
    return client, mock_qdrant


def _headers(key: str = "test"):
    return {"X-API-Key": key}


def _payload(memory: str = "hello"):
    return {
        "memory_bank": "bank",
        "memory": memory,
        "sentiment": "neutral",
        "entities": ["a"],
        "tags": ["t"],
    }


def test_save_memory_wrong_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/save_memory", json=_payload(), headers=_headers("wrong")
    )
    assert resp.status_code == 403


def test_save_memory_empty_memory(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/save_memory", json=_payload(""), headers=_headers("correct")
    )
    assert resp.status_code == 400


def test_save_memory_success(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    resp = client.post(
        "/save_memory", json=_payload(), headers=_headers("correct")
    )
    assert resp.status_code == 200
    mock_qdrant.upsert.assert_awaited_once()


def test_recall_memory(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    hit = SimpleNamespace(
        id="1",
        payload={
            "memory": "hello",
            "timestamp": "now",
            "sentiment": "neutral",
            "entities": ["a"],
            "tags": ["t"],
        },
        score=0.9,
    )
    mock_qdrant.search.return_value = [hit]
    resp = client.post(
        "/recall_memory",
        json={
            "memory_bank": "bank",
            "query": "hello",
            "entity": "a",
            "tag": "t",
            "sentiment": "neutral",
            "top_k": 5,
        },
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    assert resp.json()["results"][0]["id"] == "1"
    _, kwargs = mock_qdrant.search.await_args
    assert len(kwargs["query_filter"].must) == 3


def test_manage_memories_create(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    monkeypatch.setenv("DIM", "3")
    client, mock_qdrant = create_client()
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "create"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    mock_qdrant.create_collection.assert_awaited_once()
    assert mock_qdrant.create_payload_index.call_count == 3


def test_manage_memories_delete(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "delete"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    mock_qdrant.delete_collection.assert_awaited_once()


def test_manage_memories_forget(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    uid = str(uuid.uuid4())
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "forget", "uuid": uid},
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    mock_qdrant.delete.assert_awaited_once()


def test_manage_memories_forget_missing_uuid(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "forget"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 400
