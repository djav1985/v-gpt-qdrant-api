import pytest

import main


@pytest.mark.asyncio
async def test_startup_event_missing_env_vars(monkeypatch):
    for var in ["API_KEY", "DIM", "QDRANT_HOST", "REDIS_URL"]:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError) as exc:
        await main.startup_event()
    assert "Missing required environment variables" in str(exc.value)


@pytest.mark.asyncio
async def test_startup_event_calls_initialize(monkeypatch):
    for var in ["API_KEY", "DIM", "QDRANT_HOST", "REDIS_URL"]:
        monkeypatch.setenv(var, "value")

    init_called = False
    limiter_called = False

    async def fake_initialize():
        nonlocal init_called
        init_called = True

    async def fake_limiter_init(_):
        nonlocal limiter_called
        limiter_called = True

    monkeypatch.setattr(main, "initialize_text_embedding", fake_initialize)
    monkeypatch.setattr(main.FastAPILimiter, "init", fake_limiter_init)
    monkeypatch.setattr(main.redis, "from_url", lambda *a, **k: object())
    await main.startup_event()
    assert init_called
    assert limiter_called
