import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from dependencies import limit_concurrency
from routes.embeddings import embeddings_router
from routes.memory import memory_router

app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
)

# Applying the concurrency limit middleware (assuming it's a middleware factory)
app.add_middleware(limit_concurrency())

app.include_router(memory_router)
app.include_router(embeddings_router)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

@app.get("/v1", include_in_schema=False)
async def v1():
    return FileResponse("/app/public/index.html")
