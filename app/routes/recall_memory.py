import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient, models

from app.models import (
    SearchParams,
    RecallMemoryResponse,
    MemoryRecord,
    SentimentEnum,
)
from app.dependencies import get_embeddings_model, create_qdrant_client, get_api_key
from app.routes.common import ERROR_RESPONSES

router = APIRouter()


@router.post(
    "/recall_memory",
    operation_id="recall_memory",
    dependencies=[Depends(get_api_key)],
    response_model=RecallMemoryResponse,
    summary="Recall memories",
    description="Retrieve memories similar to a query from a memory bank.",
    tags=["memory"],
    responses={
        200: {
            "model": RecallMemoryResponse,
            "description": "Recalled memories",
        },
        **ERROR_RESPONSES,
    },
)
async def recall_memory(
    params: SearchParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> RecallMemoryResponse:
    """Retrieve memories similar to a query from a memory bank.

    Args:
        params: Search parameters including query text and filters.
        qdrant: Async Qdrant client dependency.

    Returns:
        RecallMemoryResponse: Matching memories and scores.
    """
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.query)
    # Convert iterable to list to enable indexing
    vector_list = list(vector)
    if isinstance(vector_list[0], (list, tuple)):
        vector = vector_list[0]
    else:
        vector = vector_list
    query_vector = list(map(float, vector))

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
        query_vector=query_vector,
        query_filter=models.Filter(must=filters) if filters else None,
        with_payload=True,
        limit=params.top_k,
    )
    results = []
    for hit in hits:
        payload = hit.payload or {}
        try:
            uuid_val = UUID(str(hit.id))
            sentiment_val = SentimentEnum(payload["sentiment"])
            ts_raw = payload.get("timestamp")
            if isinstance(ts_raw, str):
                timestamp_val = datetime.fromisoformat(ts_raw)
            elif isinstance(ts_raw, datetime):
                timestamp_val = ts_raw
            else:
                raise ValueError("invalid timestamp")
            memory_val = payload["memory"]
        except Exception:
            continue
        entities_val = payload.get("entities") or []
        tags_val = payload.get("tags") or []
        results.append(
            MemoryRecord(
                id=uuid_val,
                memory=memory_val,
                timestamp=timestamp_val,
                sentiment=sentiment_val,
                entities=entities_val,
                tags=tags_val,
                score=hit.score,
            )
        )
    return RecallMemoryResponse(results=results)
