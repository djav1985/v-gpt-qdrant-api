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
from dependencies import get_api_key, get_embeddings_model

# Creating an instance of the FastAPI router
memory_router = APIRouter()

# Endpoint for saving memory
@memory_router.post("/save_memory", operation_id="save_memory")
# The function below saves a memory into the Qdrant collection.
async def save_memory(params: MemoryParams, api_key: str = Depends(get_api_key)):
    try:
        # Extracting the single vector from the generatorfrom dependencies import get_api_key, get_embeddings_model

        embeddings_generator = await get_embeddings_model().embed(params.memory)

        # Fetching the first item from the generator
        vector = next(embeddings_generator)

        # Converting the vector to a list
        vector_list = vector.tolist()

        # Generating a unique ID and timestamp for the memory
        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        QdrantClient = AsyncQdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))

        # Upserting the memory into the Qdrant collection using PointStruct
        await QdrantClient.upsert(
            collection_name=params.collection_name,
            points=[
                models.PointStruct(
                    id=unique_id,
                    payload={
                        "memory": params.memory,
                        "timestamp": timestamp,
                        "sentiment": params.sentiment,
                        "entities": params.entities,
                        "tags": params.tags,
                    },
                    vector=vector_list,
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
async def recall_memory(params: SearchParams, api_key: str = Depends(get_api_key)):
    try:
        # Extracting the single vector from the generatorfrom dependencies import get_api_key, get_embeddings_model

        embeddings_generator = await get_embeddings_model().embed(params.query)

        # Fetching the first item from the generator
        vector = next(embeddings_generator)

        # Converting the vector to a list
        vector_list = vector.tolist()

        filter_conditions = []
        # Creating filter conditions based on provided parameters
        if params.entity:
            filter_conditions.append(
                models.FieldCondition(
                    key="entities",
                    match=models.MatchValue(value=params.entity)
                )
            )

        if params.sentiment:
            filter_conditions.append(
                models.FieldCondition(
                    key="sentiment",
                    match=models.MatchAny(any=[params.sentiment])
                )
            )

        if params.tag:
            filter_conditions.append(
                models.FieldCondition(
                    key="tags",
                    match=models.MatchAny(any=[params.tag])
                )
            )

        # Defining the search filter with the specified conditions
        search_filter = models.Filter(must=filter_conditions)

        QdrantClient = AsyncQdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))

        # Performing the search with the specified filters
        hits = await QdrantClient.search(
            collection_name=params.collection_name,
            query_vector=vector_list,
            query_filter=search_filter,
            with_payload=True,
            limit=params.top_k,
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
async def create_collection(params: CreateCollectionParams, api_key: str = Depends(get_api_key)):
    try:
        QdrantClient = AsyncQdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
        # Recreating the collection with specified parameters
        await QdrantClient.create_collection(
            collection_name=params.collection_name,
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
                collection_name=params.collection_name,
                field_name=field, field_schema="keyword"
            )

        return {"message": f"Collection '{params.collection_name}' created successfully"}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
