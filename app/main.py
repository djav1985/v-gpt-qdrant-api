import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from starlette.responses import FileResponse

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition
from fastembed import TextEmbedding

# Load environment variables for model, host and API keys
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
memories_api_key = os.getenv("MEMORIES_API_KEY")
base_url = os.getenv("BASE_URL")

# Initialize clients for database and AI
db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)
embeddings_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Function to get API key
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

class SearchParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to search in.")
    query: str = Field(..., description="The search query used to retrieve similar memories.")
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")

class CreateCollectionParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")


@app.post("/save_memory", operation_id="save_memory")
async def save_memory(Params: MemoryParams, api_key: str = Depends(get_api_key)):
    vector = embeddings_model.embed([Params.memory])[0]  # Corrected to index into the list of embeddings
    timestamp = datetime.utcnow().isoformat()
    unique_id = str(uuid.uuid4())
    try:
        db_client.upsert(collection_name=Params.collection_name, points=[{
            "id": unique_id,
            "vector": vector,
            "payload": {
                "memory": Params.memory,
                "timestamp": timestamp,
                "sentiment": Params.sentiment,
                "entities": Params.entities,
                "tags": Params.tags,
            },
        }])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving to Qdrant: {str(e)}")

    return {"message": "Memory saved successfully"}

@app.post("/recall_memory", operation_id="recall_memory")
async def recall_memory(Params: SearchParams, api_key: str = Depends(get_api_key)):
    query_vector = embeddings_model.embed([Params.query])[0]  # Corrected to index into the list of embeddings
    search_filter = {}
    if Params.entity:
        search_filter["must"] = [FieldCondition(key="entities", match={"value": Params.entity})]
    if Params.tag:
        search_filter["must"] = [FieldCondition(key="tags", match={"value": Params.tag})]
    if Params.sentiment:
        search_filter["must"] = [FieldCondition(key="sentiment", match={"value": Params.sentiment})]
    hits = db_client.search(
        collection_name=Params.collection_name,
        query_vector=query_vector,
        query_filter=Filter(must=search_filter["must"]) if search_filter else None,
        limit=Params.top_k,
    )
    results = [{
        "id": hit.id,
        "memory": hit.payload["memory"],
        "timestamp": hit.payload["timestamp"],
        "sentiment": hit.payload["sentiment"],
        "entities": hit.payload["entities"],
        "tags": hit.payload["tags"],
        "score": hit.score,
    } for hit in hits]
    return {"results": results}

@app.post("/collections", operation_id="collection")
async def create_collection(params: CreateCollectionParams, api_key: str = Depends(get_api_key)):
    try:
        db_client.recreate_collection(
            collection_name=params.collection_name,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )
        return {"message": f"Collection '{params.collection_name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")


class OpenaiParams(BaseModel):
    input: str
    model: str
    m_type: str = Field(..., alias='model_type', description="Type of the model such as 'text-embedding'")
    credentials: Dict

    class Config:
        populate_by_name = True  # Updated configuration for Pydantic V2

class EmbeddingParams(BaseModel):
    input: str
    model: str

    class Config:
        populate_by_name = True  # Updated configuration for Pydantic V2

@app.post("/v1")
async def authenticate_api(request: Request):
    data = await request.json()  # Asynchronously get the JSON data from the request
    print(data)  # Print the raw data to the console
    params = OpenaiParams(**data)  # Validate and parse data using Pydantic model
    return {
        "model": params.model,
        "credentials": params.credentials
    }
    
@app.post("/v1/embeddings")
async def generate_embeddings(request: Request):
    data = await request.json()  # Asynchronously get the JSON data from the request
    print(data)  # Print the raw data to the console
    params = OpenaiParams(**data)  # Validate and parse data using Pydantic model
    return {
        "model": params.model
    }
    
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

app.mount("/static", StaticFiles(directory="/app/public"), name="static")
