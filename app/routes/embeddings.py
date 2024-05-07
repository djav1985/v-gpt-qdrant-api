# routes/embeddings.py
import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastembed import TextEmbedding

# Local Imports
from models import EmbeddingParams
from dependencies import get_api_key, get_embeddings_model

# Creating an instance of the FastAPI router
embeddings_router = APIRouter()

# Semaphore to limit to 16 concurrent requests
semaphore = asyncio.Semaphore(16)

# This is the endpoint that handles embedding requests
@embeddings_router.post("/v1/embeddings", operation_id="create_embedding")
async def embedding_request(Params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    try:
        # Acquire semaphore
        await semaphore.acquire()
        
        # First, await the completion of get_embeddings_model to get the model instance
        model = await get_embeddings_model()

        # Then, use the model instance to call and await the embed method
        embeddings_generator = model.embed(Params.input)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)

        # Constructing the response data with usage details
        response_data = {
            "object": "list",
            "data": [{"object": "embedding", "embedding": vector.tolist(), "index": 0}],
            "model": os.getenv("LOCAL_MODEL"),
            "usage": {
                # Counting the tokens in the input prompt
                "prompt_tokens": len(Params.input.split()),
                # Counting the tokens in the generated vector
                "total_tokens": len(vector.tolist()),
            },
        }

        # Returning the response data
        return response_data
    except Exception as e:
        print(f"An error occurred: {e}")
        # Raising an exception if there's an error in processing the request
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
    finally:
        # Ensure the semaphore is released even if an error occurs
        semaphore.release()
