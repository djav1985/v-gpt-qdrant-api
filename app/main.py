### main.py
import os
from fastapi import FastAPI
from dependencies import initialize_text_embedding
from routes.memory import memory_router
from routes.root import root_router

app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    root_path=os.getenv("ROOT_PATH", ""),
    servers=[{"url": os.getenv("BASE_URL", ""), "description": "Base API server"}],
)


@app.on_event("startup")
async def startup_event() -> None:
    required_env_vars = ["API_KEY", "DIM", "QDRANT_HOST"]
    missing = [v for v in required_env_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    await initialize_text_embedding()


app.include_router(memory_router)
app.include_router(root_router)
