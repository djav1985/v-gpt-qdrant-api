import asyncio
from typing import List

from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from pydantic import BaseModel

from models import ErrorResponse
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
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Text must not be empty",
            "content": {
                "application/json": {
                    "example": {"detail": "Text must not be empty"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Invalid API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            },
        },
    },
)
async def create_embedding(payload: EmbeddingRequest) -> EmbeddingResponse:
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, payload.text)
    return EmbeddingResponse(embedding=vector.tolist())
