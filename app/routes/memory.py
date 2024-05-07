# /routes/memory.py
import os
import uuid
from datetime import datetime

# Importing necessary libraries and modules
from fastapi import APIRouter, Depends, HTTPException
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import (
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    PointStruct,
)

from models import SaveParams, SearchParams, ManageMemoryParams
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client

# Creating an instance of the FastAPI router
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
        model = await get_embeddings_model()
        embeddings_generator = model.embed(Params.memory)
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
        model = await get_embeddings_model()
        embeddings_generator = model.embed(Params.query)
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


# Endpoint to manage memories
@memory_router.post("/manage_memories", operation_id="manage_memories")
async def manage_memories(
    Params: ManageMemoryParams,
    api_key: str = Depends(get_api_key),
    Qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
):
    try:
        if Params.action == "create":
            # Create new memory bank in Qdrant
            await Qdrant.create_collection(
                collection_name=Params.memory_bank,
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

            # Create payload index for each field
            index_fields = ["sentiment", "entities", "tags"]
            for field in index_fields:
                await Qdrant.create_payload_index(
                    collection_name=Params.memory_bank,
                    field_name=field,
                    field_schema="keyword",
                )

            return {
                "message": f"Memory Bank '{Params.memory_bank}' created successfully"
            }

        elif Params.action == "delete":
            # Delete entire memory bank
            await Qdrant.delete_collection(collection_name=Params.memory_bank)

            return {"message": f"Memory Bank '{Params.memory_bank}' has been deleted."}

        elif Params.action == "forget":
            if Params.uuid is None:
                raise HTTPException(
                    status_code=400, detail="UUID must be provided for forget action"
                )

            # Delete specific memory using UUID
            await Qdrant.delete(
                collection_name=Params.memory_bank, point_ids=[Params.uuid]
            )

            return {
                "message": f"Memory with UUID '{Params.uuid}' has been forgotten from Memory Bank '{Params.memory_bank}'."
            }

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
