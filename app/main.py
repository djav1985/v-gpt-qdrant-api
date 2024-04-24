``

import uuidfrom datetime import datetimefrom typing import List, Optional
from fastapi import FastAPI, HTTPExceptionfrom pydantic import BaseModel, validatorfrom qdrant_client import QdrantClient
# Hardcoded configuration for vector size, distance, and HNSWVECTOR_SIZE = 1536  # Adjust based on your embedding dimensionalityDISTANCE = "cosine"HNSW_CONFIG = {    "M": 16,    "ef_construct": 100,}

# Replace with your actual valuesopenai.api_key = "{openai_api_key}"embeddings_model = "{embeddings_model}"  # e.g., "text-embedding-ada-002"qdrant_host = "{qdrant_host}"qdrant_api_key = "{qdrant_api_key}"
# Initialize Qdrant clientclient = qdrant_client.QdrantClient(host=qdrant_host, api_key=qdrant_api_key)
app = FastAPI()

class MemoryData(BaseModel):  # Changed class name    memory: str = Field(..., max_length=1024)    sentiment: str = Field(..., regex="^(positive|neutral|negative)$")    entities: List[str] = Field(..., min_items=1)    tags: List[str] = Field(..., min_items=1)    collection_name: str = Field(...)
    @validator("entities", "tags", pre=True)    def split_str_values(cls, v):        if isinstance(v, str):            return v.split(",")        return v

@app.post("/save_memory")async def save_memory(data: MemoryData):  # Changed parameter name    # Generate embedding vector    response = openai.Embedding.create(        input=data.memory, engine=embeddings_model    )    vector = response['data'][0]['embedding']
    # Create timestamp    timestamp = datetime.utcnow().isoformat()
# Create UUID    unique_id = str(uuid.uuid4())  # Generate a UUID and convert it to a string
    # Create Qdrant point    point = {        "id": unique_id,  # Use the generated UUID as the ID     "vector": vector,        "payload": {            "memory": data.memory,            "timestamp": timestamp,            "sentiment": data.sentiment,            "entities": data.entities,            "tags": data.tags,        },    }
    # Upsert point to Qdrant collection (replace if exists)    try:        client.upsert(collection_name=data.collection_name, points=[point])    except Exception as e:        raise HTTPException(status_code=500, detail=f"Error saving to Qdrant: {e}")
    return {"message": "Memory saved successfully"}```

```python# ... (previous code)

class SearchParams(BaseModel):    query: str = Field(..., max_length=1024)    entities: List[str] = Field(default_factory=list)    tags: List[str] = Field(default_factory=list)    sentiment: str = Field(default=None, regex="^(positive|neutral|negative)?$")    collection_name: str = Field(...)  # Add collection_name to SearchParams
    @validator("entities", "tags", pre=True)    def split_str_values(cls, v):        if isinstance(v, str):            return v.split(",")        return v

@app.post("/retrieve_memory")async def retrieve_memory(params: SearchParams):    

    # Generate embedding vector for the query    response = openai.Embedding.create(input=params.query, engine=embeddings_model)    query_vector = response['data'][0]['embedding']
    # Build search filter based on optional parameters    search_filter = {}    if params.entities:        search_filter["must"] = [            {"key": "entities", "match": {"value": entity}} for entity in params.entities        ]    if params.tags:        if "must" in search_filter:            search_filter["must"].extend(                [{"key": "tags", "match": {"value": tag}} for tag in params.tags]            )        else:            search_filter["must"] = [                {"key": "tags", "match": {"value": tag}} for tag in params.tags            ]    if params.sentiment:        if "must" in search_filter:            search_filter["must"].append(                {"key": "sentiment", "match": {"value": params.sentiment}}            )        else:            search_filter["must"] = [                {"key": "sentiment", "match": {"value": params.sentiment}}            ]
    # Search Qdrant for similar vectors    search_result = client.search(        collection_name=params.collection_name,        query_vector=query_vector,        limit=5,        filter=search_filter if search_filter else None,    )
# Extract results and return (including ID)    results = [        {            "id": hit.id,  # Include the ID in the results            "memory": hit.payload["memory"],            "timestamp": hit.payload["timestamp"],            "sentiment": hit.payload["sentiment"],            "entities": hit.payload["entities"],            "tags": hit.payload["tags"],            "score": hit.score,        }        for hit in search_result    ]    return {"results": results}

class CreateCollectionParams(BaseModel):    collection_name: str

@app.post("/collections")  # Endpoint path without collection_nameasync def create_collection(params: CreateCollectionParams):    try:        client.recreate_collection(collection_name=params.collection_name)        return {"message": f"Collection '{params.collection_name}' created successfully"}    except Exception as e:        raise HTTPException(status_code=500, detail=f"Error creating collection: {e}")

@app.post("/collections")
async def create_collection(params: CreateCollectionParams):
try:
# Define payload schema
payload_schema = {
"memory": {"type": "text"},
"timestamp": {"type": "date"},
"sentiment": {"type": "keyword"},
"entities": {"type": "keyword"},
"tags": {"type": "keyword"},
}

```
    client.recreate_collection(
        collection_name=params.collection_name,
        vector_size=VECTOR_SIZE,
        distance=DISTANCE,
        hnsw_config=HNSW_CONFIG,
        payload_schema=payload_schema,
    )
    return {"message": f"Collection '{params.collection_name}' created successfully"}
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error creating collection: {e}")

```

[](https://www.notion.so/73839592da524c8d8e96491fbec3ad9c?pvs=21)
