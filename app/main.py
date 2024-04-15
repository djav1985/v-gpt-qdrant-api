import openai
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from qdrant_client import QdrantClient
from qdrant_client.http.models import CollectionDescription
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

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
    keywords: Optional[str] = None  # Comma-separated keywords
    context: Optional[str] = None  # Indicates message context (AI, user, info)

class SearchData(BaseModel):
    collection: str
    number_of_results: int
    query: str
    context: Optional[str] = None  # Search based on message context (ai, user, info)
    keywords: Optional[str] = None  # Comma-separated keywords to filter search results

@app.post("/collections/")
async def manage_collection(data: CollectionAction):
    if data.action == 'create':
        # Define vectors configuration with indexing by timestamp and context
        vectors_config = CollectionDescription(
            distance="Cosine",
            indexing=[
                {"field": "metadata.timestamp", "type": "float", "params": {"dimension": 1}},
                {"field": "metadata.context", "type": "string", "params": {"dimension": 1}}
            ]
        )

        # Create or recreate the collection with the specified configuration
        response = qdrant_client.recreate_collection(
            collection_name=data.name,
            vectors_config=vectors_config
        )
    elif data.action == 'delete':
        # Delete the collection
        response = qdrant_client.delete_collection(collection_name=data.name)
    else:
        # Handle invalid action
        raise HTTPException(status_code=400, detail="Invalid action specified")

    return {"message": f"Collection '{data.name}' {data.action}d successfully", "response": response}

@app.post("/embeddings/")
async def add_embedding(data: EmbeddingData):
    # Validate context field
    valid_context_values = ["ai", "user", "info"]
    if data.context and data.context not in valid_context_values:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid context value. Valid values are: ai, user, info")

    # Validate keywords field
    if data.keywords:
        keywords_list = [keyword.strip() for keyword in data.keywords.split(',')]
        for keyword in keywords_list:
            if len(keyword.split()) > 1:  # Check if keyword contains multiple words
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keywords must be single words or multiple words separated by commas")

    # Generate timestamp
    timestamp = datetime.now()

    # Split keywords into a list
    keywords = [] if not data.keywords else [keyword.strip() for keyword in data.keywords.split(',')]

    # Add metadata including timestamp, keywords, and context
    metadata = {
        "timestamp": timestamp.isoformat(),
        "keywords": keywords,
        "context": data.context
    }

    # Generate embedding
    embeddings_response = openai.Embedding.create(
        input=data.content,
        model="text-embedding-ada-002"
    )
    embedding = embeddings_response['data'][0]['embedding']

    # Upload embedding with metadata to the collection
    response = qdrant_client.upload_collection(
        collection_name=data.collection,
        points=[{"id": 1, "vector": embedding, "metadata": metadata}]  # Ensure proper ID management in real applications
    )
    return {"message": "Embedding added successfully", "response": response}

@app.get("/search/")
async def search_embeddings(data: SearchData):
    # Initialize metadata filter
    metadata_filter = {}

    # Apply context filter if provided
    if data.context:
        metadata_filter["context"] = data.context

    # Convert space-separated string of keywords into a list if provided
    keywords_list = None if not data.keywords else [keyword.strip() for keyword in data.keywords.split(',')]

    # Initialize text filter
    text_filter = None

    # Apply keywords filter if provided
    if keywords_list:
        text_filter = keywords_list

    # Perform search with context filter, keywords filter, and query
    search_response = qdrant_client.search(
        collection_name=data.collection,
        query_vector=[float(x) for x in data.query.split()],  # Convert space-separated string of floats into a list
        top=data.number_of_results,
        metadata_filter=metadata_filter,
        text_filter=text_filter,
        text_query=data.query  # Use query for text search
    )
    return {"results": search_response}

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")