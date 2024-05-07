# dependencies.py
import os
import asyncio

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient


# Singleton class to manage a single instance of TextEmbedding
class SingletonTextEmbedding:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise Exception("SingletonTextEmbedding has not been initialized")
        return cls._instance

    @classmethod
    async def initialize(cls):
        if cls._instance is None:
            cls._instance = TextEmbedding(
                model_name=os.getenv("LOCAL_MODEL"), cache_dir="/app/models", parallel=0
            )


# Function to initialize text embedding at app startup
async def initialize_text_embedding():
    await SingletonTextEmbedding.initialize()


# Dependency to get embeddings model
def get_embeddings_model():
    return SingletonTextEmbedding.get_instance()


# Function to create Qdrant client
async def create_qdrant_client():
    return AsyncQdrantClient(
        url=os.getenv("QDRANT_HOST", "http://qdrant:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )


# This function checks if the provided API key is valid or not
async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    if os.getenv("MEMORIES_API_KEY") and (
        not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")
    ):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None
