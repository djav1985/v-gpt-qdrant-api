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

from qdrant_client import AsyncQdrantClient, models  # Asynchronous Qdrant client for non-blocking database operations
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition
from fastembed import TextEmbedding  # Library for generating embeddings from text

# Initialize TextEmbedding for AI operations
embeddings_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories in the form of text, recall them later, and perform searches. It uses an AI model to generate embeddings from text and a Qdrant database to store these embeddings along with other data.",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
)

# This function checks if the provided API key is valid or not
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# Define a custom Semaphore class with logging
class LoggingSemaphore(asyncio.Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self._waiting_tasks = 0
        self._active_tasks = 0

    async def acquire(self):
        self._waiting_tasks += 1
        await super().acquire()
        self._waiting_tasks -= 1
        self._active_tasks += 1

    def release(self):
        self._active_tasks -= 1
        super().release()

    # Get the number of waiting tasks
    def get_waiting_tasks(self):
        return self._waiting_tasks

    # Get the number of active tasks
    def get_active_tasks(self):
        return self._active_tasks

# Create an instance of the semaphore with logging
semaphore = LoggingSemaphore(int(os.getenv("API_CONCURRENCY")))

# Middleware to limit concurrency and log task status
async def limit_concurrency(request: Request, call_next):
    print(f"New Task: Active tasks now: {semaphore.get_active_tasks()}, Number of pending tasks: {semaphore.get_waiting_tasks()}")
    await semaphore.acquire()  # Acquire semaphore before processing the request
    try:
        response = await call_next(request)
        return response
    finally:
        print(f"Task Complete: Active tasks now: {semaphore.get_active_tasks()}, Number of pending tasks: {semaphore.get_waiting_tasks()}")
        semaphore.release()  # Always release semaphore after processing the request

app.middleware('http')(limit_concurrency)

# Dependency to get Qdrant client
async def get_qdrant_client(request: Request) -> AsyncQdrantClient:
    db_client = AsyncQdrantClient(
        host=os.getenv("QDRANT_HOST"),
        prefer_grpc=True,
        grpc_port=6334,
        https=False,
        api_key=os.getenv("QDRANT_API_KEY")
    )
    return db_client

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
async def save_memory(params: MemoryParams, api_key: str = Depends(get_api_key), db_client: AsyncQdrantClient = Depends(get_qdrant_client)):
    try:
        # Generate an embedding from the memory text using the AI model
        embeddings_generator = embeddings_model.embed(params.memory)
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
@app.post("/recall_memory", operation_id="recall_memory")
async def recall_memory(params: SearchParams, api_key: str = Depends(get_api_key), db_client: AsyncQdrantClient = Depends(get_qdrant_client)):
    try:
        # Generate an embedding from the query text using the AI model
        embeddings_generator = embeddings_model.embed(params.query)

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
@app.post("/collections", operation_id="create_collection")
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

# This is the endpoint that handles embedding requests
@app.post("/v1/embeddings", operation_id="create_embedding")
async def embedding_request(params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    try:
        # Generate an embedding from the memory text using the AI model
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
