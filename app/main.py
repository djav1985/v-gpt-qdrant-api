# Import necessary libraries
import os
import re
from datetime import datetime
from typing import Optional, List

import openai
from openai import OpenAI

from fastapi import FastAPI, HTTPException, Depends, Query, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator

from qdrant_client import QdrantClient
from qdrant_client.http import models
from scipy.spatial.distance import cosine

# Importing local modules assuming they contain required functionalities
from functions import load_configuration, get_text_entries, calculate_similarity_scores, generate_unique_identifier, get_qdrant_client


# Load configuration on startup
BASE_URL, API_KEY, qdrant_host, qdrant_port, qdrant_api_key, qdrant_client, openai.api_key = load_configuration()
print(f"Configuration Loaded: BASE_URL={BASE_URL}, API_KEY={API_KEY}, qdrant_host={qdrant_host}, qdrant_port={qdrant_port}")

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

class BaseDataModel(BaseModel):
    # Define the keywords field explicitly in the base model where validators are used
    keywords: Optional[List[str]] = Field(default=None)

    @validator('keywords', pre=True)
    def convert_string_to_list(cls, v):
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]  # Split and strip spaces from keywords
        return v

    @validator('keywords', each_item=True)
    def validate_keywords(cls, v):
        if v and not re.match(r'^\w+$', v):
            raise ValueError("Keywords must be single words composed of alphanumeric characters and underscores.")
        return v

class EmbeddingData(BaseDataModel):
    content: str
    collection: str
    # Inherits keywords field and its validators from BaseDataModel

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
async def add_embedding(data: EmbeddingData, qdrant_client: QdrantClient = Depends(get_qdrant_client)):
    try:
        # Initialize the OpenAI client
        client = OpenAI()

        # Generate embedding using the new OpenAI API
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=data.content,
            encoding_format="float"
        )
        embedding = response['data']

        # Generate a unique identifier for the new point
        point_id = some_unique_identifier()  # Ensure you have a method to generate unique IDs

        # Metadata including timestamp, keywords
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "keywords": data.keywords
        }

        # Upload embedding with metadata to the Qdrant collection
        upload_response = qdrant_client.upload_points(
            collection_name=data.collection,
            points=[{
                "id": point_id,
                "vector": embedding,
                "payload": metadata
            }]
        )
        return {"message": "Embedding added successfully", "response": upload_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/", operation_id="retrieve")
async def search_embeddings(data: SearchData):
    if data.keywords:
        for keyword in data.keywords:
            if ' ' in keyword:  # Check if keyword contains spaces
                raise HTTPException(status_code=400, detail="Keywords must be single words.")

    # Generate embedding for the search query using the specified model and dimensions
    try:
        response = openai.Embedding.create(
            input=data.query,
            model="text-embedding-3-large",  # Your specified model
            dimensions=128                    # Specified dimension
        )
        query_embedding = response['data'][0]['embedding']
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
