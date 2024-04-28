# Importing necessary libraries and modules
import os
import uuid
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

# Load environment variables for model, host and API keys
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
memories_api_key = os.getenv("MEMORIES_API_KEY")
base_url = os.getenv("BASE_URL")

# Initialize clients for database and AI
# QdrantClient for database interaction
db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)
# TextEmbedding for AI operations
embeddings_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Function to get API key
# This function checks if the provided API key is valid or not
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if memories_api_key and (not credentials or credentials.credentials != memories_api_key):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application to remember and recall things",
    servers=[{"url": base_url, "description": "Base API server"}]
)

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
    input: Union[List[str], str]
    model: str
    user: Optional[str] = "unassigned"
    encoding_format: Optional[str] = "float"


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
            print("Converted Vector List:", vector_list)
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

    except Exception as e:
        # Provide more detailed error messaging
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    print(f"Saved Memory: {params.memory}")
    return {"message": "Memory saved successfully"}


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
            print("Converted Vector List:", vector_list)
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
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# Endpoint for creating a new collection
@app.post("/collections", operation_id="collection")
async def create_collection(params: CreateCollectionParams, api_key: str = Depends(get_api_key)):
    try:
        # Recreate the collection with specified parameters
        db_client.recreate_collection(
            collection_name=params.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

        # Create payload index for sentiment
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="sentiment", field_schema="keyword"
        )

        # Create payload index for entities
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="entities", field_schema="keyword"
        )

        # Create payload index for tags
        db_client.create_payload_index(
            collection_name=params.collection_name,
            field_name="tags", field_schema="keyword"
        )

        print(f"Collection {params.collection_name} created successfully")
        return {"message": f"Collection '{params.collection_name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")

# Endpoint for embedding request
@app.post("/v1/embeddings")
async def embedding_request(request: EmbeddingParams, api_key: str = Depends(get_api_key)):
    # Normalize input to always be a list
    if isinstance(request.input, str):  # Fixed to request.input
        input_texts = [request.input]  # Convert single string to list
    else:
        input_texts = request.input  # It's already a list
    try:
        # Assuming embeddings_model is initialized and available globally or injected
        embeddings = [embeddings_model.embed(text) for text in input_texts]
        embeddings = []
        embedding_objects = []

        # Iterate over each set of embeddings
        for index, vectors in enumerate(embeddings):
            for vector in vectors:
                # Convert NumPy array to list for JSON serialization
                embedding_objects.append({
                    "object": "embedding",
                    "embedding": vector.tolist(),
                    "index": index
                })

        # Construct the response data
        response_data = {
            "object": "list",
            "data": embedding_objects,
            "model": request.model,
            "usage": {
                "prompt_tokens": 8,  # Total tokens processed in all inputs
                "total_tokens": 8   # Assuming no additional tokens were used
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")
    print("Response data:", response_data)
    return response_data

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Mounting static files
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
