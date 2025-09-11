# dependencies.py
import os
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient
from models import ErrorResponse


class SingletonTextEmbedding:
    """
    Singleton class to manage a single instance of the FastEmbed
    TextEmbedding model.
    """

    _instance: Optional[TextEmbedding] = None

    @classmethod
    def get_instance(cls) -> TextEmbedding:
        """
        Returns the singleton instance of TextEmbedding or raises an error
        if not initialized.
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
    Initialize the TextEmbedding singleton at application startup.
    """
    await SingletonTextEmbedding.initialize()


def get_embeddings_model() -> TextEmbedding:
    """
    FastAPI dependency to retrieve the initialized TextEmbedding model.
    """
    return SingletonTextEmbedding.get_instance()


async def create_qdrant_client() -> AsyncQdrantClient:
    """
    FastAPI dependency to create and return an async Qdrant client instance.
    """
    return AsyncQdrantClient(
        url=os.getenv("QDRANT_HOST", "http://qdrant:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )


api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(
    api_key: Optional[str] = Security(api_key_scheme),
) -> Optional[str]:
    """Validate an API key from the request header."""
    expected = os.getenv("API_KEY")
    if expected and api_key != expected:
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse(
                status=403,
                code="invalid_api_key",
                detail="Invalid or missing API key",
            ).model_dump(),
        )
    return api_key
