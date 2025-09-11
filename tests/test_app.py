import importlib
from pathlib import Path
from unittest.mock import AsyncMock

import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


def reload_main():
    import app.main as main
    importlib.reload(main)
    return main


def set_common_env(monkeypatch):
    monkeypatch.setenv("MEMORIES_API_KEY", "test")
    monkeypatch.setenv("LOCAL_MODEL", "test-model")
    monkeypatch.setenv("DIM", "384")
    monkeypatch.setenv("QDRANT_HOST", "http://localhost:6333")


def test_missing_memories_api_key(monkeypatch):
    monkeypatch.delenv("MEMORIES_API_KEY", raising=False)
    monkeypatch.setenv("LOCAL_MODEL", "model")
    monkeypatch.setenv("DIM", "384")
    monkeypatch.setenv("QDRANT_HOST", "http://localhost:6333")
    main = reload_main()
    with pytest.raises(RuntimeError):
        with TestClient(main.app):
            pass


def test_missing_local_model(monkeypatch):
    monkeypatch.setenv("MEMORIES_API_KEY", "key")
    monkeypatch.delenv("LOCAL_MODEL", raising=False)
    monkeypatch.setenv("DIM", "384")
    monkeypatch.setenv("QDRANT_HOST", "http://localhost:6333")
    main = reload_main()
    with pytest.raises(RuntimeError):
        with TestClient(main.app):
            pass


@pytest.mark.asyncio
async def test_qdrant_delete_point_ids(monkeypatch):
    set_common_env(monkeypatch)
    from app.routes.memory import manage_memories
    params = importlib.import_module("app.models").ManageMemoryParams(
        memory_bank="bank", action="forget", uuid="123"
    )
    qdrant = AsyncMock()
    await manage_memories(params=params, api_key=None, qdrant=qdrant)
    from qdrant_client import models

    qdrant.delete.assert_awaited_with(
        collection_name="bank",
        points_selector=models.PointIdsList(points=["123"]),
    )


def test_index_path_resolves(monkeypatch):
    set_common_env(monkeypatch)
    main = reload_main()
    main.initialize_text_embedding = AsyncMock()
    with TestClient(main.app) as client:
        response = client.get("/")
        assert response.status_code == 200
    index_path = Path("app/public/index.html")
    assert index_path.exists()


@pytest.mark.asyncio
async def test_create_qdrant_client_closes(monkeypatch):
    set_common_env(monkeypatch)
    closed = False

    class DummyClient:
        async def close(self):
            nonlocal closed
            closed = True

    monkeypatch.setattr(
        "app.dependencies.AsyncQdrantClient", lambda **_: DummyClient()
    )
    from app.dependencies import create_qdrant_client

    gen = create_qdrant_client()
    client = await gen.__anext__()
    assert isinstance(client, DummyClient)
    await gen.aclose()
    assert closed


@pytest.mark.asyncio
async def test_recall_memory_entity_filter(monkeypatch):
    set_common_env(monkeypatch)
    from app.routes import memory as memory_route

    class DummyModel:
        def embed(self, _):
            def g():
                import numpy as np

                yield np.array([0.0])

            return g()

    memory_route.get_embeddings_model = lambda: DummyModel()
    qdrant = AsyncMock()
    qdrant.search.return_value = []
    params = importlib.import_module("app.models").SearchParams(
        memory_bank="bank", query="hi", entity="cat", top_k=5
    )
    await memory_route.recall_memory(params=params, api_key=None, qdrant=qdrant)

    filter_used = qdrant.search.await_args.kwargs["query_filter"]
    cond = filter_used.must[0]
    from qdrant_client import models

    assert cond.key == "entities"
    assert isinstance(cond.match, models.MatchAny)
    assert cond.match.any == ["cat"]
