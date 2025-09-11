# dependencies.py
import os
from typing import Optional, AsyncGenerator

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient


class SingletonTextEmbedding:
    """
    Singleton class to manage a single instance of the FastEmbed TextEmbedding model.
    """

    _instance: Optional[TextEmbedding] = None

    @classmethod
    def get_instance(cls) -> TextEmbedding:
        """
        Returns the singleton instance of TextEmbedding, or raises an error if not initialized.
        """
        if cls._instance is None:
            raise RuntimeError("TextEmbedding model not initialized")
        return cls._instance

    @classmethod
    async def initialize(cls) -> None:
        """
        Initializes the singleton instance using environment configuration.
        """
        if cls._instance is None:
            cls._instance = TextEmbedding(
                model_name=os.getenv("LOCAL_MODEL"),
                cache_dir="/app/models",
                parallel="none",
                threads=3,
            )


async def initialize_text_embedding() -> None:
    """
    Triggers initialization of the TextEmbedding singleton at application startup.
    """
    await SingletonTextEmbedding.initialize()


def get_embeddings_model() -> TextEmbedding:
    """
    FastAPI dependency to retrieve the initialized TextEmbedding model.
    """
    return SingletonTextEmbedding.get_instance()


async def create_qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    """Yield a Qdrant client and ensure it is properly closed."""
    client = AsyncQdrantClient(
        url=os.getenv("QDRANT_HOST", "http://qdrant:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    try:
        yield client
    finally:
        await client.close()


def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[str]:
    """
    Validates an API key against the value in the environment.

    Raises:
        HTTPException: If the provided key does not match the expected key.
    """
    expected = os.getenv("MEMORIES_API_KEY")
    if expected and (not credentials or credentials.credentials != expected):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None
