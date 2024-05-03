# Importing necessary libraries and modules
import os
import uuid

import asyncio
from asyncio import Semaphore

import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Union

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from starlette.responses import FileResponse

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition
from fastembed import TextEmbedding

# Initialize clients for database and AI
# QdrantClient for database interaction
db_client = QdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
# TextEmbedding for AI operations
embeddings_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Function to get API key
# This function checks if the provided API key is valid or not
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application to remember and recall things",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
)

class LoggingSemaphore(asyncio.Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self._waiting_tasks = 0

    async def acquire(self):
        self._waiting_tasks += 1
        try:
            await super().acquire()
        finally:
            self._waiting_tasks -= 1

    def get_waiting_tasks(self):
        return self._waiting_tasks

# Semaphore for controlling access to endpoints
semaphore = Semaphore(8)

async def limit_concurrency(request: Request, call_next):
    async with semaphore:
        response = await call_next(request)
    return response

app.middleware('http')(limit_concurrency)

# Class for memory parameters
class MemoryParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")

    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

# Class for search parameters
class SearchParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to search in.")
    query: str = Field(..., description="The search query used to retrieve similar memories.")
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")

# Class for creating a new collection
class CreateCollectionParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")

# Class for embedding parameters
class EmbeddingParams(BaseModel):
    input: Union[str, List[str]]
    model: str
    user: Optional[str] = "unassigned"
    encoding_format: Optional[str] = "float"

    @validator('input', pre=True)
    def flatten_input(cls, v):
        if isinstance(v, list):
            # Join list into a single string without altering the content
            return ' '.join(v)
        return v

# Endpoint for saving memory
@app.post("/save_memory", operation_id="save_memory")
async def save_memory(params: MemoryParams, api_key: str = Depends(get_api_key)):
    try:
        # Generate an embedding from the memory text
        embeddings_generator = embeddings_model.embed(params.memory)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
        else:
            raise ValueError("The embedding is not in the expected format (np.ndarray)")

        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        # Upsert the memory into the Qdrant collection
        db_client.upsert(
            collection_name=params.collection_name,
            points=[
                {
                    "id": unique_id,
                    "payload": {
                    "memory": params.memory,
                    "timestamp": timestamp,
                    "sentiment": params.sentiment,
                    "entities": params.entities,
                    "tags": params.tags,
                    },
                "vector": vector_list,
                }
            ]
        )

        print(f"Saved Memory: {params.memory}")
        return {"message": "Memory saved successfully"}

    except Exception as e:
        print(f"An error occurred: {e}")
        # Provide more detailed error messaging
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# Endpoint for recalling memory
@app.post("/recall_memory", operation_id="recall_memory")
async def recall_memory(params: SearchParams, api_key: str = Depends(get_api_key)):
    try:
        # Generate an embedding from the query text
        embeddings_generator = embeddings_model.embed(params.query)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
        else:
            raise ValueError("The embedding is not in the expected format (np.ndarray)")

        filter_conditions = []

        # Create a filter condition for entity if it exists in params
        if params.entity:
            filter_conditions.append(
                models.FieldCondition(
                    key="entities",
                    match=models.MatchValue(value=params.entity)  # Direct value match
                )
            )

        # Create a filter condition for sentiment if it exists in params
        if params.sentiment:
            filter_conditions.append(
                models.FieldCondition(
                    key="sentiment",
                    match=models.MatchAny(any=[params.sentiment])  # Using list for MatchAny
                )
            )

        # Create a filter condition for tag if it exists in params
        if params.tag:
            filter_conditions.append(
                models.FieldCondition(
                    key="tags",
                    match=models.MatchAny(any=[params.tag])  # Using list for MatchAny
                )
            )

        # Define the search filter with the specified conditions
        search_filter = models.Filter(
            must=filter_conditions
        )

        # Perform the search with the specified filters
        hits = db_client.search(
            collection_name=params.collection_name,
            query_vector=vector_list,
            query_filter=search_filter,
            with_payload=True,
            limit=params.top_k,
            search_params=models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=False,
                    rescore=True,
                    oversampling=2.0,
                )
            ),
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

        print("Recalled Memories:", results)
        return {"results": results}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# This is the endpoint that handles requests to create a new collection
@app.post("/collections", operation_id="create_collection")
async def create_collection(params: CreateCollectionParams, api_key: str = Depends(get_api_key)):
    try:
        # Recreate the collection with specified parameters
        db_client.create_collection(
            collection_name=params.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),  # Configure vector parameters
            quantization_config=models.ScalarQuantization(  # Configure scalar quantization
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=0.99,
                    always_ram=False,
                ),
            ),
        )

        # Create payload index for sentiment
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="sentiment", field_schema="keyword"  # Index for sentiment
        )

        # Create payload index for entities
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="entities", field_schema="keyword"  # Index for entities
        )

        # Create payload index for tags
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="tags", field_schema="keyword"  # Index for tags
        )

        print(f"Collection {params.collection_name} created successfully")  # Log the successful creation of the collection
        return {"message": f"Collection '{params.collection_name}' created successfully"}  # Return a success message
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")  # Raise an exception if there's an error in creating the collection

# This is the endpoint that handles embedding requests
@app.post("/v1/embeddings", operation_id="create_embedding")
async def embedding_request(params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    try:
        # Generate an embedding from the memory text
        embeddings_generator = embeddings_model.embed(params.input)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
        else:
            raise ValueError("The embedding is not in the expected format (np.ndarray)")  # Exception handling for unexpected formats

        # Construct the response data with usage details
        response_data = {
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": vector_list,
                "index": 0
            }],
            "model": params.model,
            "usage": {
                "prompt_tokens": len(params.input.split()),  # Count of tokens in the input prompt
                "total_tokens": len(vector_list)  # Count of tokens in the generated vector
            }
        }

        print("Created Embedding Successfully")  # Log the response data

        return response_data  # Return the response data
    except Exception as e:
        print(f"An error occurred: {e}")
        # Provide more detailed error messaging
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")  # Raise an exception if there's an error in processing the request

# This is the root endpoint that serves the main page of your web application
@app.get("/", include_in_schema=False)
async def root():
    # Returns the index.html file found in the specified directory
    return FileResponse("/app/public/index.html")

# This is the v1 endpoint that serves the main page of your web application
# It could be used for versioning of the API
@app.get("/v1", include_in_schema=False)
async def v1():
    # Returns the index.html file found in the specified directory
    return FileResponse("/app/public/index.html")

# Mounting static files
# This makes all the files in the /app/public directory accessible under the /static path
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
