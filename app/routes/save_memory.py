import asyncio
import uuid
from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient, models

from app.models import SaveParams, SaveMemoryResponse, ErrorResponse
from app.dependencies import (
    get_embeddings_model,
    create_qdrant_client,
    get_api_key,
)
from app.routes.common import ERROR_RESPONSES

router = APIRouter()


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
    model = get_embeddings_model()
    raw_vector = await asyncio.to_thread(model.embed, params.memory)
    vector = np.array(raw_vector, dtype=float).flatten().tolist()
    uuid_str = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        await qdrant.upsert(
            collection_name=params.memory_bank,
            points=[
                models.PointStruct(
                    id=uuid_str,
                    vector=vector,
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
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status=500,
                code="qdrant_upsert_failed",
                detail=str(exc),
            ).model_dump(),
        ) from exc
    return SaveMemoryResponse(message="Memory saved successfully")
