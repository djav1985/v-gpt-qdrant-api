# Import necessary libraries
import openai
from os import getenv  # Environment variables
from fastapi import FastAPI, HTTPException, status, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from qdrant_client import QdrantClient
from qdrant_client.http.models import CollectionDescription
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from scipy.spatial.distance import cosine


# Importing local modules
from functions import load_configuration

# Load configuration on startup
BASE_URL, API_KEY, qdrant_host, qdrant_port, qdrant_api_key, openai_api_key, qdrant_client = load_configuration()

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
    keywords: Optional[str] = Query(None, regex=r'^(\w+(,\s*\w+)*)?$')  # Comma-separated keywords or single word
    context: Optional[str] = Query(None, regex=r'^ai|user|info$')  # Indicates message context (ai, user, info)

class SearchData(BaseModel):
    collection: str
    number_of_results: int
    query: str
    context: Optional[str] = Query(None, regex=r'^ai|user|info$')  # Search based on message context (ai, user, info)
    keywords: Optional[str] = Query(None, regex=r'^(\w+(,\s*\w+)*)?$')  # Comma-separated keywords or single word to filter search results

@app.post("/collections/", operation_id="manage_collections")
async def manage_collection(data: CollectionAction):
    try:
        if data.action == 'create':
            # Ensure you replace 'YourCollectionName' with the appropriate logic to set collection names
            vectors_config = CollectionDescription(
                name=data.name,  # Set the collection name dynamically based on input
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
            return {"message": f"Collection '{data.name}' created successfully", "response": response}

        elif data.action == 'delete':
            # Delete the collection
            response = qdrant_client.delete_collection(collection_name=data.name)
            return {"message": f"Collection '{data.name}' deleted successfully", "response": response}

        else:
            raise HTTPException(status_code=400, detail="Invalid action specified")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/", operation_id="save")
async def add_embedding(data: EmbeddingData):
    # Validate input data
    if data.keywords:
        keywords_list = [keyword.strip() for keyword in data.keywords.split(',')]
        for keyword in keywords_list:
            if len(keyword.split()) > 1:  # Check if keyword contains multiple words
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keywords must be single words or multiple words separated by commas")

    # Generate embedding with specified dimensions
    embeddings_response = openai.Embedding.create(
        input=data.content,
        model="text-embedding-3-large",
        dimensions=256
    )
    embedding = embeddings_response['data'][0]['embedding']

    # Generate metadata including timestamp, keywords, and context
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "keywords": data.keywords.split(',') if data.keywords else [],
        "context": data.context
    }

    # Upload embedding with metadata to the collection
    response = qdrant_client.upload_collection(
        collection_name=data.collection,
        points=[{"id": 1, "vector": embedding, "metadata": metadata}]  # Ensure proper ID management in real applications
    )
    return {"message": "Embedding added successfully", "response": response}

@app.get("/search/", operation_id="retrieve")
async def search_embeddings(data: SearchData):
    # Validate input data
    if data.keywords:
        keywords_list = [keyword.strip() for keyword in data.keywords.split(',')]
        for keyword in keywords_list:
            if len(keyword.split()) > 1:  # Check if keyword contains multiple words
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keywords must be single words or multiple words separated by commas")

    # Generate embedding for the search query
    query_embedding_response = openai.Embedding.create(
        input=data.query,
        model="text-embedding-3-large",
        dimensions=256
    )
    query_embedding = query_embedding_response['data'][0]['embedding']

    # Retrieve text entries from the vector database based on search criteria
    text_entries = get_text_entries(data.collection, data.context, data.keywords)

    # Filter text entries based on context and keywords if provided
    filtered_text_entries = filter_text_entries(text_entries, data.context, data.keywords)

    # Calculate similarity scores between query embedding and filtered text entry embeddings
    search_results = []
    for text_entry in filtered_text_entries:
        entry_embedding = text_entry['embedding']
        similarity_score = 1 - cosine(query_embedding, entry_embedding)
        search_results.append({"text_entry": text_entry, "similarity_score": similarity_score})

    # Rank search results based on similarity scores
    search_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Return top-ranked search results
    return {"results": search_results[:data.number_of_results]}

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
