# routes/memory.py
import os
import uuid
from datetime import datetime

# Third-Party Library Imports
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, PointStruct

# Local Imports
from models import MemoryParams, SearchParams, CreateCollectionParams
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client

# Creating an instance of the FastAPI router
memory_router = APIRouter()

# Endpoint for saving memory
@memory_router.post("/save_memory", operation_id="save_memory")
# The function below saves a memory into the Qdrant collection.
async def save_memory(Params: MemoryParams, api_key: str = Depends(get_api_key), Qdrant: AsyncQdrantClient = Depends(create_qdrant_client)):
    try:
        # First, await the completion of get_embeddings_model to get the model instance
        model = await get_embeddings_model()

        # Then, use the model instance to call and await the embed method
        embeddings_generator = model.embed(Params.memory)

        # Fetching the first item from the generator
        vector = next(embeddings_generator)

        # Generating a unique ID and timestamp for the memory
        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        # Upserting the memory into the Qdrant collection using PointStruct
        await Qdrant.upsert(
            collection_name=Params.collection_name,
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
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Endpoint for recalling memory
@memory_router.post("/recall_memory", operation_id="recall_memory")
# The function below recalls a memory from the Qdrant collection based on provided search parameters.
async def recall_memory(Params: SearchParams, api_key: str = Depends(get_api_key), Qdrant: AsyncQdrantClient = Depends(create_qdrant_client)):
    try:
        # First, await the completion of get_embeddings_model to get the model instance
        model = await get_embeddings_model()

        # Then, use the model instance to call and await the embed method
        embeddings_generator = model.embed(Params.query)

        # Fetching the first item from the generator
        vector = next(embeddings_generator)

        filter_conditions = []
        # Creating filter conditions based on provided parameters
        if Params.entity:
            filter_conditions.append(
                models.FieldCondition(
                    key="entities",
                    match=models.MatchValue(value=Params.entity)
                )
            )

        if Params.sentiment:
            filter_conditions.append(
                models.FieldCondition(
                    key="sentiment",
                    match=models.MatchAny(any=[Params.sentiment])
                )
            )

        if Params.tag:
            filter_conditions.append(
                models.FieldCondition(
                    key="tags",
                    match=models.MatchAny(any=[Params.tag])
                )
            )

        # Defining the search filter with the specified conditions
        search_filter = models.Filter(must=filter_conditions)

        # Performing the search with the specified filters
        hits = await Qdrant.search(
            collection_name=Params.collection_name,
            query_vector=vector.tolist(),
            query_filter=search_filter,
            with_payload=True,
            limit=Params.top_k,
            search_params=models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=False,
                    rescore=True,
                    oversampling=2.0
                )
            )
        )

        # Formatting the results
        results = [{
            "id": hit.id,
            "memory": hit.payload["memory"],
            "timestamp": hit.payload["timestamp"],
            "sentiment": hit.payload["sentiment"],
            "entities": hit.payload["entities"],
            "tags": hit.payload["tags"],
            "score": hit.score,
        } for hit in hits]

        return {"results": results}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# This is the endpoint that handles requests to create a new collection
@memory_router.post("/collections", operation_id="create_collection")
# The function below creates a new collection in Qdrant with specified parameters.
async def create_collection(Params: CreateCollectionParams, api_key: str = Depends(get_api_key), Qdrant: AsyncQdrantClient = Depends(create_qdrant_client)):
    try:
        # Recreating the collection with specified parameters
        await Qdrant.create_collection(
            collection_name=Params.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=0.99,
                    always_ram=False,
                ),
            ),
        )

        # Creating payload index for sentiment, entities, and tags
        index_fields = ["sentiment", "entities", "tags"]
        for field in index_fields:
            await QdrantClient.create_payload_index(
                collection_name=Params.collection_name,
                field_name=field, field_schema="keyword"
            )

        return {"message": f"Collection '{Params.collection_name}' created successfully"}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
