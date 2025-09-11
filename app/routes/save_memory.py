import asyncio
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient, models

from models import (
    SaveParams,
    SaveMemoryResponse,
    ErrorResponse,
)
from dependencies import get_embeddings_model, create_qdrant_client, get_api_key

router = APIRouter()

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    403: {"model": ErrorResponse, "description": "Forbidden"},
    404: {"model": ErrorResponse, "description": "Not Found"},
    422: {"model": ErrorResponse, "description": "Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}


@router.post(
    "/save_memory",
    operation_id="save_memory",
    dependencies=[Depends(get_api_key)],
    response_model=SaveMemoryResponse,
    summary="Save a memory",
    description="Store a memory with sentiment, entities, and tags in a memory bank.",
    tags=["memory"],
    responses={
        200: {
            "model": SaveMemoryResponse,
            "description": "Memory saved successfully",
        },
        **ERROR_RESPONSES,
    },
)
async def save_memory(
    params: SaveParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> SaveMemoryResponse:
    if not params.memory.strip():
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                status=400,
                code="memory_empty",
                detail="Memory content cannot be empty",
            ).model_dump(),
        )

    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.memory)
    uuid_str = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    await qdrant.upsert(
        collection_name=params.memory_bank,
        points=[
            models.PointStruct(
                id=uuid_str,
                vector=vector.tolist(),
                payload={
                    "memory": params.memory,
                    "timestamp": timestamp,
                    "sentiment": params.sentiment,
                    "entities": params.entities,
                    "tags": params.tags,
                },
            )
        ],
    )
    return SaveMemoryResponse(message="Memory saved successfully")
