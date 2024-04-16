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

ai_client = OpenAI(
    api_key=os.environ['OPENAI_API_KEY']
)

qdrant_client = QdrantClient(
    url="http://qdrant:6333",
    api_key=os.getenv("QDRANT_API_KEY")
)

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
    action: str
    name: str

class EmbeddingData(BaseModel):
    memories: list[str]  # List of texts for embedding
    collection: str

class SearchData(BaseDataModel):
    collection: str
    query: str

@app.post("/collections/", operation_id="manage_collections")
async def manage_collection(data: CollectionAction):
    print(f"Request to manage collection received with action: {data.action} and name: {data.name}")

    try:
        if data.action == 'create':
            print(f"Preparing to create a collection named '{data.name}'")

            # Create or recreate the collection with the specified configuration
            response = qdrant_client.create_collection(
            collection_name=data.collection,
            vectors_config=models.VectorParams(size=128, distance=models.Distance.COSINE)
            )

            print(f"Collection '{data.name}' successfully created with response: {response}")
            return {"message": f"Collection '{data.name}' created successfully", "response": response}

        elif data.action == 'delete':
            print(f"Preparing to delete a collection named '{data.name}'")
            response = qdrant_client.delete_collection(collection_name=data.name)
            print(f"Collection '{data.name}' successfully deleted with response: {response}")
            return {"message": f"Collection '{data.name}' deleted successfully", "response": response}

        else:
            print(f"Invalid action specified: {data.action}")
            raise HTTPException(status_code=400, detail="Invalid action specified")

    except Exception as e:
        print(f"Error handling the {data.action} action for the collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/", operation_id="save")
async def add_embedding(data: EmbeddingData):
    try:
        # Initialize the OpenAI client
        ai_client = OpenAI()

        # Generate embeddings for all provided texts
        response = ai_client.Embedding.create(input=data.memories, model="text-embedding-ada")

        # Prepare points for insertion into Qdrant
        points = [
            PointStruct(
                id=idx,
                vector=entry['embedding'],
                payload={
                    "memory": memory,  # Using 'memory' instead of 'text'
                    "timestamp": datetime.now().isoformat()
                }
            )
            for idx, (entry, memory) in enumerate(zip(response['data'], data.memories))  # Renamed 'text' to 'memory'
        ]

        # Insert all points into the specified collection in Qdrant
        qdrant_client.upsert(data.collection, points)

        return {"message": "Embeddings added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/", operation_id="retrieve")
async def search_embeddings(data: SearchData):
    try:
        # Initialize the OpenAI client
        ai_client = OpenAI()

        # Generate embedding for the query
        query_embedding_response = ai_client.Embedding.create(input=data.query, model="text-embedding-ada")
        query_vector = query_embedding_response['data'][0]['embedding']

        # Perform the search using the query vector
        search_results = qdrant_client.search(
            data.collection,
            search_params=models.SearchParams(hnsw_ef=128, exact=False),
            query_vector=query_vector,
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
