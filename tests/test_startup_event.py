import pytest

from app import main


def test_lifespan_missing_env_vars(monkeypatch):
    async def run():
        for var in ["API_KEY", "DIM", "QDRANT_HOST"]:
            monkeypatch.delenv(var, raising=False)
        from app.config import get_settings

        get_settings.cache_clear()
        with pytest.raises(RuntimeError) as exc:
            async with main.lifespan(main.app):
                pass
        assert "Missing required environment variables" in str(exc.value)

    import asyncio

    asyncio.run(run())


def test_lifespan_calls_initialize(monkeypatch):
    async def run():
        for var in ["API_KEY", "QDRANT_HOST"]:
            monkeypatch.setenv(var, "value")
        monkeypatch.setenv("DIM", "10")
        from app.config import get_settings

        get_settings.cache_clear()

        init_called = False

        async def fake_initialize():
            nonlocal init_called
            init_called = True

        monkeypatch.setattr(main, "initialize_text_embedding", fake_initialize)
        async with main.lifespan(main.app):
            pass
        assert init_called
        assert main.app.state.dim == 10

    import asyncio

    asyncio.run(run())


def test_lifespan_invalid_dim(monkeypatch):
    async def run():
        monkeypatch.setenv("API_KEY", "value")
        monkeypatch.setenv("QDRANT_HOST", "value")
        monkeypatch.setenv("DIM", "notint")
        from app.config import get_settings

        get_settings.cache_clear()
        with pytest.raises(RuntimeError) as exc:
            async with main.lifespan(main.app):
                pass
        assert "DIM must be an integer" in str(exc.value)

    import asyncio

    asyncio.run(run())
