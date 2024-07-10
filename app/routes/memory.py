# /routes/memory.py
import uuid
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient, models

from models import SaveParams, SearchParams
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client

memory_router = APIRouter()


# Endpoint to save memory
@memory_router.post("/save_memory", operation_id="save_memory")
async def save_memory(
    Params: SaveParams,
    api_key: str = Depends(get_api_key),
    Qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
):
    try:
        # Get model and generate embeddings
        model = get_embeddings_model()
        embeddings_generator = await asyncio.to_thread(model.embed, Params.memory)
        vector = next(embeddings_generator)

        # Create unique id and timestamp
        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        # Save memory in Qdrant
        await Qdrant.upsert(
            collection_name=Params.memory_bank,
            points=[
                models.PointStruct(
                    id=unique_id,
                    payload={
                        "memory": Params.memory,
                        "timestamp": timestamp,
                        "sentiment": Params.sentiment,
                        "entities": Params.entities,
                        "tags": Params.tags,
                    },
                    vector=vector.tolist(),
                ),
            ],
        )
        return {"message": "Memory saved successfully"}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


# Endpoint to recall memory
@memory_router.post("/recall_memory", operation_id="recall_memory")
async def recall_memory(
    Params: SearchParams,
    api_key: str = Depends(get_api_key),
    Qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
):
    try:
        # Get model and generate embeddings
        model = get_embeddings_model()
        embeddings_generator = await asyncio.to_thread(model.embed, Params.query)
        vector = next(embeddings_generator)

        # Create filter conditions
        filter_conditions = []
        if Params.entity:
            filter_conditions.append(
                models.FieldCondition(
                    key="entities", match=models.MatchValue(value=Params.entity)
                )
            )
        if Params.sentiment:
            filter_conditions.append(
                models.FieldCondition(
                    key="sentiment", match=models.MatchAny(any=[Params.sentiment])
                )
            )
        if Params.tag:
            filter_conditions.append(
                models.FieldCondition(
                    key="tags", match=models.MatchAny(any=[Params.tag])
                )
            )

        # Perform search in Qdrant
        search_filter = models.Filter(must=filter_conditions)
        hits = await Qdrant.search(
            collection_name=Params.memory_bank,
            query_vector=vector.tolist(),
            query_filter=search_filter,
            with_payload=True,
            limit=Params.top_k,
            search_params=models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=False, rescore=True, oversampling=2.0
                )
            ),
        )

        # Format results
        results = [
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

        return {"results": results}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
