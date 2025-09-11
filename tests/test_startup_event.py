import pytest

import main


@pytest.mark.asyncio
async def test_lifespan_missing_env_vars(monkeypatch):
    for var in ["API_KEY", "DIM", "QDRANT_HOST"]:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError) as exc:
        async with main.lifespan(main.app):
            pass
    assert "Missing required environment variables" in str(exc.value)


@pytest.mark.asyncio
async def test_lifespan_calls_initialize(monkeypatch):
    for var in ["API_KEY", "QDRANT_HOST"]:
        monkeypatch.setenv(var, "value")
    monkeypatch.setenv("DIM", "10")

    init_called = False

    async def fake_initialize():
        nonlocal init_called
        init_called = True

    monkeypatch.setattr(main, "initialize_text_embedding", fake_initialize)
    async with main.lifespan(main.app):
        pass
    assert init_called
    assert main.app.state.dim == 10


@pytest.mark.asyncio
async def test_lifespan_invalid_dim(monkeypatch):
    monkeypatch.setenv("API_KEY", "value")
    monkeypatch.setenv("QDRANT_HOST", "value")
    monkeypatch.setenv("DIM", "notint")
    with pytest.raises(RuntimeError) as exc:
        async with main.lifespan(main.app):
            pass
    assert "DIM must be an integer" in str(exc.value)
