import asyncio
from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter
from qdrant_client import AsyncQdrantClient, models

from models import (
    SearchParams,
    RecallMemoryResponse,
    MemoryRecord,
    ErrorResponse,
)
from dependencies import get_embeddings_model, create_qdrant_client, get_api_key

router = APIRouter()
rate_limiter = RateLimiter(times=10, seconds=60)

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
    "/recall_memory",
    operation_id="recall_memory",
    dependencies=[Depends(rate_limiter), Depends(get_api_key)],
    response_model=RecallMemoryResponse,
    summary="Recall memories",
    description="Retrieve memories similar to a query from a memory bank.",
    tags=["memory"],
    responses={
        200: {
            "model": RecallMemoryResponse,
            "description": "Recalled memories",
            "headers": RATE_LIMIT_HEADERS,
        },
        **ERROR_RESPONSES,
    },
)
async def recall_memory(
    params: SearchParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> RecallMemoryResponse:
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.query)

    filters = []
    if params.entity:
        filters.append(
            models.FieldCondition(
                key="entities", match=models.MatchValue(value=params.entity)
            )
        )
    if params.sentiment:
        filters.append(
            models.FieldCondition(
                key="sentiment", match=models.MatchAny(any=[params.sentiment])
            )
        )
    if params.tag:
        filters.append(
            models.FieldCondition(
                key="tags",
                match=models.MatchAny(any=[params.tag]),
            )
        )

    hits = await qdrant.search(
        collection_name=params.memory_bank,
        query_vector=vector.tolist(),
        query_filter=models.Filter(must=filters) if filters else None,
        with_payload=True,
        limit=params.top_k,
    )
    return RecallMemoryResponse(
        results=[
            MemoryRecord(
                id=hit.id,
                memory=hit.payload["memory"],
                timestamp=hit.payload["timestamp"],
                sentiment=hit.payload["sentiment"],
                entities=hit.payload["entities"],
                tags=hit.payload["tags"],
                score=hit.score,
            )
            for hit in hits
        ]
    )
