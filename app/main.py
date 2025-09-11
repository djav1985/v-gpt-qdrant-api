# main.py
import os

from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from dependencies import initialize_text_embedding
from routes.memory import memory_router  # noqa: E402
from routes.root import root_router  # noqa: E402

app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    root_path=os.getenv("ROOT_PATH", ""),
    servers=[
        {"url": os.getenv("BASE_URL", ""), "description": "Base API server"}
    ],
)


@app.on_event("startup")
async def startup_event() -> None:
    required_env_vars = ["API_KEY", "DIM", "QDRANT_HOST", "REDIS_URL"]
    missing = [v for v in required_env_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(
        redis_url, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_client)
    await initialize_text_embedding()


app.include_router(memory_router)
if os.getenv("EMBEDDING_ENDPOINT"):
    from routes.embeddings import embeddings_router

    app.include_router(embeddings_router)

app.include_router(root_router)
