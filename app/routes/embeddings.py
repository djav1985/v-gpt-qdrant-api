import asyncio
from typing import List

from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from pydantic import BaseModel

from dependencies import get_embeddings_model, get_api_key

embeddings_router = APIRouter()


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]


@embeddings_router.post(
    "/embeddings",
    operation_id="create_embedding",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=60)),
        Depends(get_api_key),
    ],
    response_model=EmbeddingResponse,
    summary="Generate embeddings for text",
    tags=["embedding"],
)
async def create_embedding(payload: EmbeddingRequest) -> EmbeddingResponse:
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, payload.text)
    return EmbeddingResponse(embedding=vector.tolist())
