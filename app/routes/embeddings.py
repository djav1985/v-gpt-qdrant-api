import asyncio
from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from models import EmbeddingRequest, EmbeddingResponse, ErrorResponse
from dependencies import get_embeddings_model, get_api_key

router = APIRouter()
rate_limiter = RateLimiter(times=5, seconds=60)

RATE_LIMIT_HEADERS = {
    "X-RateLimit-Limit": {"$ref": "#/components/headers/X-RateLimit-Limit"},
    "X-RateLimit-Remaining": {"$ref": "#/components/headers/X-RateLimit-Remaining"},
    "X-RateLimit-Reset": {"$ref": "#/components/headers/X-RateLimit-Reset"},
}

ERROR_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "Bad Request",
        "headers": RATE_LIMIT_HEADERS,
    },
    401: {
        "model": ErrorResponse,
        "description": "Unauthorized",
        "headers": RATE_LIMIT_HEADERS,
    },
    403: {
        "model": ErrorResponse,
        "description": "Forbidden",
        "headers": RATE_LIMIT_HEADERS,
    },
    404: {
        "model": ErrorResponse,
        "description": "Not Found",
        "headers": RATE_LIMIT_HEADERS,
    },
    422: {
        "model": ErrorResponse,
        "description": "Validation Error",
        "headers": RATE_LIMIT_HEADERS,
    },
    429: {
        "model": ErrorResponse,
        "description": "Too Many Requests",
        "headers": RATE_LIMIT_HEADERS,
    },
    500: {
        "model": ErrorResponse,
        "description": "Internal Server Error",
        "headers": RATE_LIMIT_HEADERS,
    },
}


@router.post(
    "/embeddings",
    operation_id="create_embedding",
    dependencies=[Depends(rate_limiter), Depends(get_api_key)],
    response_model=EmbeddingResponse,
    summary="Generate embeddings for text",
    description="Generate an embedding vector for the provided text.",
    tags=["embedding"],
    responses={
        200: {
            "model": EmbeddingResponse,
            "description": "Embedding vector",
            "headers": RATE_LIMIT_HEADERS,
        },
        **ERROR_RESPONSES,
    },
)
async def create_embedding(payload: EmbeddingRequest) -> EmbeddingResponse:
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, payload.text)
    return EmbeddingResponse(embedding=vector.tolist())
