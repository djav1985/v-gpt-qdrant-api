import os
import uuid
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, PointStruct

from models import UnifiedParams
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client

memory_router = APIRouter()

@memory_router.post("/", operation_id="manage-memory", dependencies=[Depends(get_api_key)])
async def manage_memory(params: UnifiedParams, api_key: str = Depends(get_api_key), Qdrant: AsyncQdrantClient = Depends(create_qdrant_client)):
    try:
        operation_type = params.root.operation_type
        details = params.root

        if operation_type == "save_memory":
            model = get_embeddings_model()
            embeddings_generator = await asyncio.to_thread(model.embed, details.memory)
            vector = next(embeddings_generator)
            timestamp = datetime.utcnow().isoformat()
            unique_id = str(uuid.uuid4())

            await Qdrant.upsert(
                collection_name=details.memory_bank,
                points=[
                    models.PointStruct(
                        id=unique_id,
                        payload={
                            "memory": details.memory,
                            "timestamp": timestamp,
                            "sentiment": details.sentiment,
                            "entities": details.entities,
                            "tags": details.tags,
                        },
                        vector=vector.tolist(),
                    ),
                ],
            )
            return {"message": "Memory saved successfully"}

        elif operation_type == "recall_memory":
            model = get_embeddings_model()
            embeddings_generator = await asyncio.to_thread(model.embed, details.query)
            vector = next(embeddings_generator)
            filter_conditions = []

            if details.entity:
                filter_conditions.append(models.FieldCondition(key="entities", match=models.MatchValue(value=details.entity)))
            if details.sentiment:
                filter_conditions.append(models.FieldCondition(key="sentiment", match=models.MatchAny(any=[details.sentiment])))
            if details.tag:
                filter_conditions.append(models.FieldCondition(key="tags", match=models.MatchAny(any=[details.tag])))

            search_filter = models.Filter(must=filter_conditions)
            hits = await Qdrant.search(
                collection_name=details.memory_bank,
                query_vector=vector.tolist(),
                query_filter=search_filter,
                with_payload=True,
                limit=details.top_k,
                search_params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        ignore=False, rescore=True, oversampling=2.0
                    )
                ),
            )

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

        elif operation_type == "create_memory_bank":
            await Qdrant.create_collection(
                collection_name=details.memory_bank,
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

            index_fields = ["sentiment", "entities", "tags"]
            for field in index_fields:
                await Qdrant.create_payload_index(
                    collection_name=details.memory_bank,
                    field_name=field,
                    field_schema="keyword",
                )

            return {"message": f"Memory Bank '{details.memory_bank}' created successfully"}

        elif operation_type == "delete_memory_bank":
            await Qdrant.delete_collection(collection_name=details.memory_bank)
            return {"message": f"Memory Bank '{details.memory_bank}' has been deleted."}

        elif operation_type == "forget_memory":
            if details.uuid is None:
                raise HTTPException(status_code=400, detail="UUID must be provided for forget action")

            await Qdrant.delete(collection_name=details.memory_bank, points_selector=[details.uuid])
            return {"message": f"Memory with UUID '{details.uuid}' has been forgotten from Memory Bank '{details.memory_bank}'."}

        else:
            raise HTTPException(status_code=400, detail="Invalid operation type")

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
