import os
import uuid
import numpy as np
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, PointStruct
from fastembed import TextEmbedding

from models import MemoryParams, SearchParams, CreateCollectionParams
from dependencies import get_api_key, get_qdrant_client, get_embeddings_model

memory_router = APIRouter()

# Endpoint for saving memory
@memory_router.post("/save_memory", operation_id="save_memory")
async def save_memory(params: MemoryParams, api_key: str = Depends(get_api_key), db_client: AsyncQdrantClient = Depends(get_qdrant_client)):
    try:
        # Generate an embedding from the memory text using the AI model
        embeddings_generator = get_embeddings_model().embed(params.memory)
    
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
        else:
            raise ValueError("The embedding is not in the expected format (np.ndarray)")

        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        # Upsert the memory into the Qdrant collection using PointStruct
        await db_client.upsert(
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
async def recall_memory(params: SearchParams, api_key: str = Depends(get_api_key), db_client: AsyncQdrantClient = Depends(get_qdrant_client)):
    try:
        # Generate an embedding from the query text using the AI model
        embeddings_generator = get_embeddings_model().embed(params.query)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if not isinstance(vector, np.ndarray):
            raise ValueError("The embedding is not in the expected format (np.ndarray)")

        vector_list = vector.tolist()  # Convert numpy array to list

        filter_conditions = []
        # Create filter conditions based on provided parameters
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

        # Define the search filter with the specified conditions
        search_filter = models.Filter(must=filter_conditions)

        # Perform the search with the specified filters
        hits = await db_client.search(
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

        # Format the results
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
async def create_collection(params: CreateCollectionParams, api_key: str = Depends(get_api_key), db_client: AsyncQdrantClient = Depends(get_qdrant_client)):
    try:
        # Recreate the collection with specified parameters
        await db_client.create_collection(
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

        # Create payload index for sentiment, entities, and tags
        index_fields = ["sentiment", "entities", "tags"]
        for field in index_fields:
            await db_client.create_payload_index(
                collection_name=params.collection_name,
                field_name=field, field_schema="keyword"
            )

        return {"message": f"Collection '{params.collection_name}' created successfully"}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
