import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastembed import TextEmbedding

from dependencies import limit_concurrency
from routes.embeddings import embeddings_router
from routes.memory import memory_router

# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories in the form of text, recall them later, and perform searches. It uses an AI model to generate embeddings from text and a Qdrant database to store these embeddings along with other data.",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
)

app.middleware('http')(limit_concurrency)

app.include_router(memory_router)

app.include_router(embeddings_router)

app.mount("/static", StaticFiles(directory="/app/public"), name="static")

# This is the root endpoint that serves the main page of your web application
@app.get("/", include_in_schema=False)
async def root():
    # Returns the index.html file found in the specified directory
    return FileResponse("/app/public/index.html")

# This is the v1 endpoint that serves the main page of your web application
# It could be used for versioning of the API
@app.get("/v1", include_in_schema=False)
async def v1():
    # Returns the index.html file found in the specified directory
    return FileResponse("/app/public/index.html")
