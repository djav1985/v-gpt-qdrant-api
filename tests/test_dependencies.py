import pytest
from fastapi import HTTPException

from app import dependencies
from app.config import get_settings


class DummyEmbed:
    def embed(self, text: str):
        return [0.1]


@pytest.fixture(autouse=True)
def reset_singleton():
    dependencies.SingletonTextEmbedding._instance = None
    yield
    dependencies.SingletonTextEmbedding._instance = None


def test_get_instance_pre_init_raises():
    with pytest.raises(RuntimeError):
        dependencies.SingletonTextEmbedding.get_instance()


def test_get_instance_after_initialize(monkeypatch):
    async def run():
        monkeypatch.setattr(
            dependencies, "TextEmbedding", lambda *args, **kwargs: DummyEmbed()
        )
        await dependencies.initialize_text_embedding()
        instance = dependencies.SingletonTextEmbedding.get_instance()
        assert isinstance(instance, DummyEmbed)

    import asyncio

    asyncio.run(run())


class DummyClient:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def test_create_qdrant_client_closes(monkeypatch):
    async def run():
        dummy = DummyClient()
        monkeypatch.setattr(
            dependencies, "AsyncQdrantClient", lambda *args, **kwargs: dummy
        )
        monkeypatch.setenv("QDRANT_HOST", "http://example")
        get_settings.cache_clear()
        gen = dependencies.create_qdrant_client()
        client = await gen.__anext__()
        assert client is dummy
        await gen.aclose()
        assert dummy.closed

    import asyncio

    asyncio.run(run())


def test_get_api_key_valid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    get_settings.cache_clear()
    assert dependencies.get_api_key("secret") == "secret"


def test_get_api_key_invalid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    get_settings.cache_clear()
    with pytest.raises(HTTPException):
        dependencies.get_api_key("wrong")


def test_get_api_key_missing(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    get_settings.cache_clear()
    with pytest.raises(HTTPException):
        dependencies.get_api_key(None)
