# Import necessary libraries
import os

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from qdrant_client.http import models

from fastapi import FastAPI, HTTPException, Depends, Query, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFilesfrom pydantic import BaseModel, Field, validator

from scipy.spatial.distance import cosine
from datetime import datetime
from openai import OpenAI
from typing import Optional, List

# Importing local modules assuming they contain required functionalities
from functions import load_configuration, get_text_entries, calculate_similarity_scores


# Load configuration on startup
BASE_URL, API_KEY = load_configuration()

ai_client = openai.OpenAI(
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
    number_of_results: int
    query: str
    # Inherits keywords field and its validators from BaseDataModel

@app.post("/collections/", operation_id="manage_collections")
async def manage_collection(data: CollectionAction):
    print(f"Request to manage collection received with action: {data.action} and name: {data.name}")

    try:
        if data.action == 'create':
            print(f"Preparing to create a collection named '{data.name}'")

            # Create or recreate the collection with the specified configuration
            response = qdrant_client.create_collection(
                collection_name=data.name,
                vectors_config={
                    "history" : models.VectorParams(size=128, distance=models.Distance.COSINE),
                    "info" : models.VectorParams(size=128, distance=models.Distance.COSINE),
                }
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
async def search_embeddings(data: SearchData, qdrant_client: QdrantClient = Depends(get_qdrant_client)):
    # Generate embedding for the search query using the specified model and dimensions
    try:
        # Initialize the OpenAI client
        client = OpenAI()

        response = client.embeddings.create(
            model="text-embedding-3-large",  # Your specified model
            input=data.query,
            encoding_format="float",
            dimensions=128                    # Specified dimension
        )
        query_embedding = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

    # Retrieve and process text entries (this part needs actual implementation details)
    text_entries = get_text_entries(data.collection, data.keywords)  # Assuming you have this function implemented

    # Calculate similarity and prepare results
    search_results = calculate_similarity_scores(text_entries, query_embedding)

    # Sort and return top results
    search_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return {"results": search_results[:data.number_of_results]}

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
