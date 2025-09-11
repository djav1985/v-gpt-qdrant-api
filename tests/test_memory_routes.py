import os
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qdrant_client.http.exceptions import ApiException as QdrantException

from app.routes.save_memory import router as save_memory_router
from app.routes.recall_memory import router as recall_memory_router
from app.routes.manage_memories import router as manage_memories_router
from app.dependencies import create_qdrant_client, get_embeddings_model
from app.config import get_settings
from app.models import (
    SaveMemoryResponse,
    RecallMemoryResponse,
    ManageMemoryResponse,
)
from qdrant_client import models


class DummyModel:
    def embed(self, text: str):
        return [0.1, 0.2, 0.3]


def create_client(model_cls=DummyModel):
    get_settings.cache_clear()
    os.environ.setdefault("DIM", "3")
    os.environ.setdefault("QDRANT_HOST", "http://localhost")
    mock_qdrant = Mock()
    mock_qdrant.upsert = AsyncMock()
    mock_qdrant.search = AsyncMock()
    mock_qdrant.create_collection = AsyncMock()
    mock_qdrant.create_payload_index = AsyncMock()
    mock_qdrant.delete_collection = AsyncMock()
    mock_qdrant.delete = AsyncMock()

    app = FastAPI()
    app.include_router(save_memory_router)
    app.include_router(recall_memory_router)
    app.include_router(manage_memories_router)

    async def override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[create_qdrant_client] = override_qdrant
    app.dependency_overrides[get_embeddings_model] = lambda: model_cls()

    import app.routes.save_memory as save_module
    import app.routes.recall_memory as recall_module
    save_module.get_embeddings_model = lambda: model_cls()
    recall_module.get_embeddings_model = lambda: model_cls()

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
        "/save_memory",
        json=_payload(),
        headers=_headers("wrong"),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == {
        "status": 403,
        "code": "invalid_api_key",
        "detail": "Invalid or missing API key",
    }


def test_save_memory_empty_memory(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/save_memory",
        json=_payload(""),
        headers=_headers("correct"),
    )
    assert resp.status_code == 422


def test_save_memory_success(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    resp = client.post(
        "/save_memory",
        json=_payload(),
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    data = SaveMemoryResponse.model_validate(resp.json())
    assert data.uuid
    mock_qdrant.upsert.assert_awaited_once()


def test_save_memory_flattens_vector(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")

    class NestedModel:
        def embed(self, text: str):
            return [[0.4, 0.5]]

    client, mock_qdrant = create_client(model_cls=NestedModel)
    resp = client.post(
        "/save_memory",
        json=_payload(),
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    args, kwargs = mock_qdrant.upsert.await_args
    assert kwargs["points"][0].vector == [0.4, 0.5]


def test_save_memory_upsert_failure(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    mock_qdrant.upsert.side_effect = QdrantException("fail")
    resp = client.post(
        "/save_memory",
        json=_payload(),
        headers=_headers("correct"),
    )
    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "qdrant_upsert_failed"


def test_recall_memory(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    hit = SimpleNamespace(
        id=str(uuid.uuid4()),
        payload={
            "memory": "hello",
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
    RecallMemoryResponse.model_validate(resp.json())
    assert resp.json()["results"][0]["id"] == hit.id
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
    ManageMemoryResponse.model_validate(resp.json())
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
    ManageMemoryResponse.model_validate(resp.json())
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
    ManageMemoryResponse.model_validate(resp.json())
    mock_qdrant.delete.assert_awaited_once()
    _, kwargs = mock_qdrant.delete.await_args
    assert isinstance(kwargs["points_selector"], models.PointIdsList)
    assert kwargs["points_selector"].points == [uid]


def test_manage_memories_forget_missing_uuid(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "forget"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 422


def test_manage_memories_invalid_action(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "invalid"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 422


def test_recall_memory_rejects_extra_field(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    resp = client.post(
        "/recall_memory",
        json={"memory_bank": "bank", "query": "hi", "unexpected": "x"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 422


def test_save_memory_rejects_extra_field(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, _ = create_client()
    data = _payload()
    data["unexpected"] = "value"
    resp = client.post(
        "/save_memory",
        json=data,
        headers=_headers("correct"),
    )
    assert resp.status_code == 422


def test_manage_memories_rejects_extra_field(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    monkeypatch.setenv("DIM", "3")
    client, _ = create_client()
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "create", "foo": "bar"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 422


def test_manage_memories_delete_failure(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    mock_qdrant.delete_collection.side_effect = QdrantException("fail")
    resp = client.post(
        "/manage_memories",
        json={"memory_bank": "bank", "action": "delete"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "qdrant_delete_failed"


def test_recall_memory_skips_invalid_payload(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    bad_hit = SimpleNamespace(
        id=str(uuid.uuid4()),
        payload={"memory": "hi", "timestamp": "not-a-date", "sentiment": "neutral"},
        score=0.1,
    )
    mock_qdrant.search.return_value = [bad_hit]
    resp = client.post(
        "/recall_memory",
        json={"memory_bank": "bank", "query": "hi"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_recall_memory_invalid_sentiment(monkeypatch):
    monkeypatch.setenv("API_KEY", "correct")
    client, mock_qdrant = create_client()
    bad_hit = SimpleNamespace(
        id=str(uuid.uuid4()),
        payload={
            "memory": "hi",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sentiment": "bad",
        },
        score=0.1,
    )
    mock_qdrant.search.return_value = [bad_hit]
    resp = client.post(
        "/recall_memory",
        json={"memory_bank": "bank", "query": "hi"},
        headers=_headers("correct"),
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []
