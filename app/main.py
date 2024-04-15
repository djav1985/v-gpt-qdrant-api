import openai
import os
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from qdrant_client import QdrantClient
from qdrant_client.http.models import CollectionDescription
from pydantic import BaseModel

# Importing local modules
from functions import load_configuration

# Load configuration on startup
BASE_URL, API_KEY, qdrant_host, qdrant_port, qdrant_api_key, openai_api_key, qdrant_client, openai.api_key = load_configuration()

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Async function to get the API key from the request
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    # If the API key is not provided or does not match the expected value, return a 403 error
    if API_KEY and (not credentials or credentials.credentials != API_KEY):
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")

    # Return the provided API key, or None if it was not provided
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
    collection: str
    content: str

class SearchData(BaseModel):
    collection: str
    number_of_results: int
    query: str

@app.post("/collections/")
async def manage_collection(data: CollectionAction):
    if data.action == 'create':
        response = qdrant_client.recreate_collection(
            collection_name=data.name,
            vectors_config=CollectionDescription(
                distance="Cosine",
            )
        )
    elif data.action == 'delete':
        response = qdrant_client.delete_collection(collection_name=data.name)
    else:
        raise HTTPException(status_code=400, detail="Invalid action specified")
    return {"message": f"Collection '{data.name}' {data.action}d successfully", "response": response}

@app.post("/embeddings/")
async def add_embedding(data: EmbeddingData):
    embeddings_response = openai.Embedding.create(
        input=data.content,
        model="text-embedding-ada-002"
    )
    embedding = embeddings_response['data'][0]['embedding']
    response = qdrant_client.upload_collection(
        collection_name=data.collection,
        points=[{"id": 1, "vector": embedding}]  # Ensure proper ID management in real applications
    )
    return {"message": "Embedding added successfully", "response": response}

@app.get("/search/")
async def search_embeddings(data: SearchData):
    search_response = qdrant_client.search(
        collection_name=data.collection,
        query_vector=[float(x) for x in data.query.split()],  # Convert space-separated string of floats into a list
        top=data.number_of_results
    )
    return {"results": search_response}

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")