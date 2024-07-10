# dependencies.py
import os
import asyncio
import numpy as np
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient
from sklearn.neighbors import NearestNeighbors

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
                model_name=os.getenv("LOCAL_MODEL"), cache_dir="/app/models", parallel="none", threads=3
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
        api_key=os.getenv("QDRANT_API_KEY")
    )

# This function checks if the provided API key is valid or not


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)),
):
    if os.getenv("MEMORIES_API_KEY") and (
        not credentials or credentials.credentials != os.getenv(
            "MEMORIES_API_KEY")
    ):
        raise HTTPException(
            status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# Function to compute dynamic `eps` and `min_samples` for DBSCAN


def compute_dynamic_dbscan_params(vectors, k=5):
    nearest_neighbors = NearestNeighbors(n_neighbors=k)
    neighbors = nearest_neighbors.fit(vectors)
    distances, indices = neighbors.kneighbors(vectors)
    distances = np.sort(distances[:, k-1], axis=0)
    # Example heuristic: 90th percentile
    eps = distances[int(0.9 * len(distances))]

    # Dynamically determine min_samples as a small fraction of the dataset size
    # At least 2, or 1% of the dataset size
    min_samples = max(2, len(vectors) // 100)

    return eps, min_samples
