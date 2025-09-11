import pytest

import main


@pytest.mark.asyncio
async def test_startup_event_missing_env_vars(monkeypatch):
    for var in ["API_KEY", "DIM", "QDRANT_HOST"]:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError) as exc:
        await main.startup_event()
    assert "Missing required environment variables" in str(exc.value)


@pytest.mark.asyncio
async def test_startup_event_calls_initialize(monkeypatch):
    for var in ["API_KEY", "DIM", "QDRANT_HOST"]:
        monkeypatch.setenv(var, "value")

    init_called = False

    async def fake_initialize():
        nonlocal init_called
        init_called = True

    monkeypatch.setattr(main, "initialize_text_embedding", fake_initialize)
    await main.startup_event()
    assert init_called
