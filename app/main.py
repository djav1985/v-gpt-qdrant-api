import os
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Importing dependencies and routers
from dependencies import initialize_text_embedding
from routes.embeddings import embeddings_router
from routes.memory import memory_router
from routes.root import root_router

# Initializing FastAPI application with title, version, description and base server URL
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}],
)


@app.on_event("startup")
async def startup_event():
    # Initialize the text embedding singleton
    await initialize_text_embedding()


# Including Routers for different endpoints
app.include_router(memory_router)

app.include_router(root_router)

# Mounting static files directory
app.mount("/static", StaticFiles(directory="/app/public"), name="static")

# Conditionally include the root_router based on EMBEDDING_ENDPOINT env var
if os.getenv("EMBEDDING_ENDPOINT") == "true":
   app.include_router(embeddings_router)
