import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Loading environment variables
embeddings_model = os.getenv("EMBEDDINGS_MODEL")  # e.g., "text-embedding-ada-002"
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
base_url = os.getenv("BASE_URL")

# Initialize clients
db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)
ai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),
)
# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application to remember and recall things",
    servers=[{"url": base_url, "description": "Base API server"}]
)

# The MemoryData class is a Pydantic model that represents the data structure of a memory.
# It includes fields for the content of the memory, its associated sentiment, identified entities, and associated tags.
class MemoryData(BaseModel):
    # The name of the collection to be created.
    collection_name: str = Field(..., description="The name of the collection to be created.")
    # The content of the memory to be stored.
    memory: str = Field(..., description="The content of the memory to be stored.")

    # The sentiment associated with the memory (e.g., positive, negative, neutral).
    sentiment: str = Field(..., description="The sentiment associated with the memory (e.g., positive, negative, neutral).")

    # A list of entities identified in the memory.
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")

    # A list of tags associated with the memory.
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")

    # Validator for "entities" and "tags" fields. If the value is a string, it splits it into a list of strings.
    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

# The SearchParams class is a Pydantic model representing the search parameters.
# It includes fields for the search query, the number of most similar memories to return, collection name, and optional search filters.
class SearchParams(BaseModel):
    # The search query used to retrieve similar memories.
    query: str = Field(..., description="The search query used to retrieve similar memories.")

    # The number of most similar memories to return.
    top_k: int = Field(..., description="The number of most similar memories to return.")

    # The name of the collection to search in.
    collection_name: str = Field(..., description="The name of the collection to search in.")

    # Optional search filters
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")


# The CreateCollectionParams class is a Pydantic model representing the parameters for creating a collection.
# It includes a field for the name of the collection to be created.
class CreateCollectionParams(BaseModel):
    # The name of the collection to be created.
    collection_name: str = Field(..., description="The name of the collection to be created.")

@app.post("/save_memory")
async def save_memory(data: MemoryData):
    # Generate embedding vector
    response = ai_client.embeddings.create(
        input=data.memory, model=embeddings_model, dimensions=1536
    )

    # Extract vector from response
    vector = response.data[0].embedding  # Use dot notation to access data and embedding attributes

    # Create timestamp
    timestamp = datetime.utcnow().isoformat()

    # Create UUID
    unique_id = str(uuid.uuid4())

    # Create Qdrant point
    point = {
        "id": unique_id,
        "vector": vector,
        "payload": {
            "memory": data.memory,
            "timestamp": timestamp,
            "sentiment": data.sentiment,
            "entities": data.entities,
            "tags": data.tags,
        },
    }

    # Upsert point to Qdrant collection (replace if exists)
    try:
        db_client.upsert(collection_name=data.collection_name, points=[point])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving to Qdrant: {e}")

    return {"message": "Memory saved successfully"}

@app.post("/retrieve_memory")
async def retrieve_memory(params: SearchParams):
    # Generate embedding vector for the query
    response = ai_client.embeddings.create(input=params.query, model=embeddings_model)
    query_vector = response.data[0].embedding  # Assuming the embedding is nested within the 'data' attribute

    # Build search filter based on optional parameters
    search_filter = {}
    if params.entity:
        search_filter["must"] = [{"key": "entities", "match": {"value": params.entity}}]
    if params.tag:
        if "must" in search_filter:
            search_filter["must"].append({"key": "tags", "match": {"value": params.tag}})
        else:
            search_filter["must"] = [{"key": "tags", "match": {"value": params.tag}}]
    if params.sentiment:
        if "must" in search_filter:
            search_filter["must"].append(
                {"key": "sentiment", "match": {"value": params.sentiment}}
            )
        else:
            search_filter["must"] = [{"key": "sentiment", "match": {"value": params.sentiment}}]

    # Search Qdrant for similar vectors
    search_result = db_client.search(
        collection_name=params.collection_name,
        query_vector=query_vector,
        limit=5,
        filter=search_filter if search_filter else None,
    )

    # Extract results and return (including ID)
    results = [
        {
            "id": hit.id,  # Include the ID in the results
            "memory": hit.payload["memory"],
            "timestamp": hit.payload["timestamp"],
            "sentiment": hit.payload["sentiment"],
            "entities": hit.payload["entities"],
            "tags": hit.payload["tags"],
            "score": hit.score,
        }
        for hit in search_result
    ]
    return {"results": results}

@app.post("/collections")  # Define a POST route at "/collections"
async def create_collection(params: CreateCollectionParams):
    try:
        # Recreate the collection with specified vector parameters
        db_client.recreate_collection(
            collection_name=params.collection_name,  # Name of the new collection
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),  # Vector configuration for the new collection
        )

        # Return a success message if the collection is created successfully
        return {"message": f"Collection '{params.collection_name}' created successfully"}
    except Exception as e:
        # If there is an error in creating the collection, raise an HTTP exception with status code 500
        raise HTTPException(status_code=500, detail=f"Error creating collection: {e}")
