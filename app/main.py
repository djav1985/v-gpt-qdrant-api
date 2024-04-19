# Import necessary libraries
import os

from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct

from fastapi import FastAPI, HTTPException, Depends, Query, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field, validator

from scipy.spatial.distance import cosine
from datetime import datetime
from openai import OpenAI
from typing import Optional, List

# Importing local modules assuming they contain required functionalities
from functions import load_configuration

# Load configuration on startup
BASE_URL, API_KEY = load_configuration()

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Async function to get the API key from the request
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if API_KEY and (not credentials or credentials.credentials != API_KEY):
        print("API key validation failed")
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
    print("API key validated successfully")
    return credentials.credentials if credentials else None


# FastAPI application instance setup
app = FastAPI(
    title="Qdrant API",
    version="0.1.0",
    description="A FastAPI application for Qdrant",
    servers=[{"url": BASE_URL, "description": "Base API server"}]
)

class CollectionAction(BaseModel):
    action: str = Field(..., description="Can be Create or Delete")
    collection: str

class EmbeddingData(BaseModel):
    memories: str = Field(..., description="Key moments from conversations, user preferences, details about the user's life, activities, and significant life events—everything you'd want to always remember.")
    sentiment: str = Field(..., description="The sentiment associated with the memory, can be positive, neutral, or negative.")
    entities: str = Field(..., description="Comma-separated list of People, Places Or Things relevant to the memory.")
    tags: str = Field(..., description="Comma-separated list of tags for categorization and search of the memory.")
    collection: str

class SearchData(BaseModel):
    query: str = Field(None, description="Query to search memories relevant to the current conversation")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment: positive, neutral, negative")
    entity: Optional[str] = Field(None, description="Filter by a single entity")
    tag: Optional[str] = Field(None, description="Filter by a single tag")
    collection: str

@app.post("/collections/", operation_id="manage_collections")
async def manage_collection(data: CollectionAction):
    print(f"Request to manage collection received with action: {data.action} and name: {data.collection}")

    try:
        if data.action == 'create':
            print(f"Preparing to create a collection named '{data.collection}'")
            qdrant_client = QdrantClient(
            url=f"http://gpt-qdrant:6333",
            api_key=os.getenv("QDRANT_API_KEY")
            )

            # Create or recreate the collection with the specified configuration
            response = qdrant_client.create_collection(
            collection_name=data.collection,
            vectors_config=models.VectorParams(size=128, distance=models.Distance.COSINE)
            )

            print(f"Collection '{data.collection}' successfully created with response: {response}")
            return {"message": f"Collection '{data.collection}' created successfully", "response": response}

        elif data.action == 'delete':
            print(f"Preparing to delete a collection named '{data.collection}'")
            qdrant_client = QdrantClient(
            url=f"http://gpt-qdrant:6333",
            api_key=os.getenv("QDRANT_API_KEY")
            )

            response = qdrant_client.delete_collection(collection_name=data.collection)
            print(f"Collection '{data.collection}' successfully deleted with response: {response}")
            return {"message": f"Collection '{data.collection}' deleted successfully", "response": response}

        else:
            print(f"Invalid action specified: {data.action}")
            raise HTTPException(status_code=400, detail="Invalid action specified")

    except Exception as e:
        print(f"Error handling the {data.action} action for the collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/", operation_id="save_memory")
async def add_embedding(data: EmbeddingData):
    try:
        # Initialize the OpenAI client
        ai_client = OpenAI(
        api_key=os.environ['OPENAI_API_KEY']
        )

        # Generate embeddings for all provided texts
        response = ai_client.embeddings.create(input=[data.memory], model="text-embedding-3-small", dimensions=128)

        # Convert comma-separated strings into lists
        entities_list = data.entities.split(',')
        tags_list = data.tags.split(',')

        # Prepare point for insertion into Qdrant
        point = PointStruct(
            # ID will be automatically generated by Qdrant if not provided
            vector=response.data[0].embedding,
            payload={
                "memory": data.memory,
                "timestamp": datetime.now().isoformat(),
                "sentiment": data.sentiment,
                "entities": entities_list,
                "tags": tags_list
            }
        )

        qdrant_client = QdrantClient(
        url=f"http://gpt-qdrant:6333",
        api_key=os.getenv("QDRANT_API_KEY")
        )

        # Insert all points into the specified collection in Qdrant
        qdrant_client.upsert(data.collection, [point])

        return {"message": "Embeddings added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/", operation_id="retrieve_memories")
async def search_embeddings(data: SearchData):
    try:
        # Initialize the OpenAI client
        ai_client = OpenAI(
            api_key=os.environ['OPENAI_API_KEY']
        )

        # Generate embedding for the query
        response = ai_client.embeddings.create(input=[data.query], model="text-embedding-3-small", dimensions=128)

        qdrant_client = QdrantClient(
            url=f"http://gpt-qdrant:6333",
            api_key=os.getenv("QDRANT_API_KEY")
        )

        # Define a filter based on optional parameters
        filters = []
        if data.sentiment:
            filters.append(models.Filter(key="sentiment", match={"value": data.sentiment}))
        if data.entity:
            filters.append(models.Filter(key="entities", match={"value": data.entity}))
        if data.tag:
            filters.append(models.Filter(key="tags", match={"value": data.tag}))

        # Combine filters into a payload
        if filters:
            filter_payload = models.Filter(must=filters)
        else:
            filter_payload = None

        # Perform the search using the query vector
        search_results = qdrant_client.search(
            data.collection,
            search_params=models.SearchParams(hnsw_ef=128, exact=False),
            query_vector=response.data[0].embedding,
            filter=filter_payload,
            limit=5
        )

        return search_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
