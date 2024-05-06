import os
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

# Importing dependencies and routers
from dependencies import limit_concurrency, initialize_text_embedding, reconnect_qdrant_client
from routes.embeddings import embeddings_router
from routes.memory import memory_router
from routes.root import root_router

# Initializing FastAPI application with title, version, description and base server URL
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
)

@app.on_event("startup")
# The function below initializes text embedding at the startup of the application.
async def startup_event():
    await initialize_text_embedding()

# Applying the concurrency limit middleware (assuming it's a middleware factory)
app.middleware('http')(limit_concurrency)

# Including Routers for different endpoints
app.include_router(memory_router)
app.include_router(embeddings_router)
app.include_router(root_router)

# Mounting static files directory
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
