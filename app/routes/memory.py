import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from fastapi_limiter.depends import RateLimiter
from pydantic import ValidationError

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams

from models import SaveParams, SearchParams, ManageMemoryParams
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client

memory_router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


# --- Save Memory ---
@memory_router.post(
    "/save_memory",
    operation_id="save_memory",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def save_memory(
    params: SaveParams,
    api_key: str = Depends(api_key_header),
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> Dict[str, str]:
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

    if not params.memory.strip():
        raise HTTPException(status_code=400, detail="Memory content cannot be empty")

    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.memory)
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


# --- Recall Memory ---
@memory_router.post(
    "/recall_memory",
    operation_id="recall_memory",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def recall_memory(
    params: SearchParams,
    api_key: str = Depends(api_key_header),
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> Dict[str, List[Dict[str, Any]]]:
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

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
            models.FieldCondition(key="tags", match=models.MatchAny(any=[params.tag]))
        )

    hits = await qdrant.search(
        collection_name=params.memory_bank,
        query_vector=vector.tolist(),
        query_filter=models.Filter(must=filters) if filters else None,
        with_payload=True,
        limit=params.top_k,
    )

    return {
        "results": [
            {
                "id": hit.id,
                "memory": hit.payload["memory"],
                "timestamp": hit.payload["timestamp"],
                "sentiment": hit.payload["sentiment"],
                "entities": hit.payload["entities"],
                "tags": hit.payload["tags"],
                "score": hit.score,
            }
            for hit in hits
        ]
    }


# --- Manage Memories ---
@memory_router.post(
    "/manage_memories",
    operation_id="manage_memories",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def manage_memories(
    params: ManageMemoryParams,
    api_key: str = Depends(api_key_header),
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> Dict[str, str]:
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

    if not params.memory_bank.isidentifier():
        raise HTTPException(status_code=400, detail="Invalid memory bank name")

    if params.action == "create":
        await asyncio.gather(
            qdrant.create_collection(
                collection_name=params.memory_bank,
                vectors_config=VectorParams(
                    size=int(os.getenv("DIM")),
                    distance=Distance.COSINE,
                ),
            ),
            *[
                qdrant.create_payload_index(
                    collection_name=params.memory_bank,
                    field_name=field,
                    field_schema="keyword",
                )
                for field in ["sentiment", "entities", "tags"]
            ],
        )
        return {"message": f"Memory Bank '{params.memory_bank}' created successfully"}

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
