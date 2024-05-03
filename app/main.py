import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from starlette.responses import FileResponse

from openai import OpenAI
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, Vectorparams, Filter, FieldCondition, Range

# Initialize clients
db_client = QdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
ai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if os.getenv("API_KEY") and (not credentials or credentials.credentials != os.getenv("API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# FastAPI application instance
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application to remember and recall things",
    servers=[{"url": os.getenv("BASE_URL"), "description": "Base API server"}]
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

@app.post("/save_memory", operation_id="save_memory")
async def save_memory(params: Memoryparams, api_key: str = Depends(get_api_key)):
    try:
        # Generate embedding vector
        response = ai_client.embeddings.create(
            input=params.memory, model=os.getenv("EMBEDDINGS_MODEL"), dimensions=512
        )

        # Extract vector from response
        vector = response.data[0].embedding  # Use dot notation to access data and embedding attributes

        # Create timestamp
        timestamp = datetime.utcnow().isoformat()

        # Create UUID
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
                "vector": vector,
                }
            ]
        )
        print(f"Saved Memory: {params.memory}")
        return {"message": "Memory saved successfully"}

    except Exception as e:
        print(f"An error occurred: {e}")
        # Provide more detailed error messaging
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/recall_memory", operation_id="recall_memory")
async def recall_memory(params: Searchparams, api_key: str = Depends(get_api_key)):
    try:
        # Generate embedding vector for the query
        response = ai_client.embeddings.create(input=params.query, model=os.getenv("EMBEDDINGS_MODEL"), dimensions=512)
        query_vector = response.data[0].embedding  # Assuming the embedding is nested within the 'data' attribute

        # Build search filter based on optional parameters
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
            search_params=models.Searchparams(
                quantization=models.QuantizationSearchparams(
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
async def create_collection(params: CreateCollectionparams, api_key: str = Depends(get_api_key)):
    try:
        # Recreate the collection with specified parameters
        db_client.create_collection(
            collection_name=params.collection_name,
            vectors_config=Vectorparams(size=128, distance=Distance.COSINE),  # Configure vector parameters
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

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
