import asyncio
from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient, models

from app.models import SearchParams, RecallMemoryResponse, MemoryRecord
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
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.query)
    # Ensure vector is a numpy array before calling tolist
    import numpy as np
    query_vector = np.array(vector, dtype=float).flatten().tolist()

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
    from uuid import UUID
    from app.models import SentimentEnum
    from datetime import datetime
    for hit in hits:
        payload = hit.payload or {}
        # Defensive defaults for all fields
        try:
            uuid_val = UUID(str(hit.id))
        except Exception:
            uuid_val = UUID("00000000-0000-0000-0000-000000000000")
        memory_val = payload.get("memory") or ""
        timestamp_val = payload.get("timestamp")
        if isinstance(timestamp_val, str):
            try:
                timestamp_val = datetime.fromisoformat(timestamp_val)
            except Exception:
                timestamp_val = datetime.now()
        elif not isinstance(timestamp_val, datetime):
            timestamp_val = datetime.now()
        sentiment_val = payload.get("sentiment") or SentimentEnum.NEUTRAL
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
