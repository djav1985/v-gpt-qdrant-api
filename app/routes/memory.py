# /routes/memory.py
import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams

from models import (
    SaveParams,
    SearchParams,
    ManageMemoryParams,
    MessageResponse,
    RecallMemoryResponse,
)
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client


memory_router = APIRouter()


# --- Save Memory ---
@memory_router.post(
    "/save_memory",
    operation_id="save_memory",
    summary="Store a memory",
    response_model=MessageResponse,
    tags=["memory"],
    responses={
        400: {"description": "Memory content cannot be empty"},
        500: {"description": "Error saving memory"},
    },
)
async def save_memory(
    params: SaveParams,
    api_key: str = Depends(get_api_key),
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> MessageResponse:
    """Store a new memory in the specified memory bank."""
    if not params.memory.strip():
        raise HTTPException(status_code=400, detail="Memory content cannot be empty")

    try:
        model = get_embeddings_model()
        embeddings_generator = await asyncio.to_thread(model.embed, params.memory)
        vector = next(embeddings_generator)

        uuid_str = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

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
        return {"message": "Memory saved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving memory: {str(e)}")


# --- Recall Memory ---
@memory_router.post(
    "/recall_memory",
    operation_id="recall_memory",
    summary="Recall memories",
    response_model=RecallMemoryResponse,
    tags=["memory"],
    responses={500: {"description": "Error recalling memory"}},
)
async def recall_memory(
    params: SearchParams,
    api_key: str = Depends(get_api_key),
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> RecallMemoryResponse:
    """Retrieve memories similar to the provided query."""
    try:
        model = get_embeddings_model()
        embeddings_generator = await asyncio.to_thread(model.embed, params.query)
        vector = next(embeddings_generator)

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
                    key="tags", match=models.MatchAny(any=[params.tag])
                )
            )

        hits = await qdrant.search(
            collection_name=params.memory_bank,
            query_vector=vector.tolist(),
            query_filter=models.Filter(must=filters) if filters else None,
            with_payload=True,
            limit=params.top_k,
            search_params=models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=False, rescore=True, oversampling=2.0
                )
            ),
        )

        return {
            "results": [
                {
                    "id": hit.id,
                    "memory": hit.payload.get("memory"),
                    "timestamp": hit.payload.get("timestamp"),
                    "sentiment": hit.payload.get("sentiment"),
                    "entities": hit.payload.get("entities"),
                    "tags": hit.payload.get("tags"),
                    "score": hit.score,
                }
                for hit in hits
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalling memory: {str(e)}")


# --- Manage Memories ---
@memory_router.post(
    "/manage_memories",
    operation_id="manage_memories",
    summary="Manage memory banks",
    response_model=MessageResponse,
    tags=["memory"],
    responses={500: {"description": "Error managing memories"}},
)
async def manage_memories(
    params: ManageMemoryParams,
    api_key: str = Depends(get_api_key),
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> MessageResponse:
    """Create, delete, or forget memories within a memory bank."""
    try:
        if params.action == "create":
            await qdrant.create_collection(
                collection_name=params.memory_bank,
                vectors_config=VectorParams(
                    size=int(os.getenv("DIM")), distance=Distance.COSINE
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=False,
                    ),
                ),
            )

            for field in ["sentiment", "entities", "tags"]:
                await qdrant.create_payload_index(
                    collection_name=params.memory_bank,
                    field_name=field,
                    field_schema="keyword",
                )

            return {
                "message": f"Memory Bank '{params.memory_bank}' created successfully"
            }

        elif params.action == "delete":
            await qdrant.delete_collection(collection_name=params.memory_bank)
            return {"message": f"Memory Bank '{params.memory_bank}' has been deleted."}

        elif params.action == "forget":
            if not params.uuid:
                raise HTTPException(
                    status_code=400, detail="UUID must be provided for forget action"
                )
            await qdrant.delete(
                collection_name=params.memory_bank,
                points_selector=[params.uuid],
            )
            return {
                "message": f"Memory with UUID '{params.uuid}' has been forgotten from Memory Bank '{params.memory_bank}'."
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error managing memories: {str(e)}")
