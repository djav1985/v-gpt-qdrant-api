# routes/embeddings.py
import os
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException

# Local Imports
from models import EmbeddingParams
from dependencies import get_api_key, get_embeddings_model

# Creating an instance of the FastAPI router
embeddings_router = APIRouter()

# Semaphore to limit to a dynamically configured number of concurrent requests
# Directly using the environment variable with a default fallback
semaphore = asyncio.Semaphore(int(os.getenv("API_CONCURRENCY", "16")))


@embeddings_router.post("/v1/embeddings", operation_id="create_embedding")
async def embedding_request(
    Params: EmbeddingParams, api_key: str = Depends(get_api_key)
):
    start_time = time.time()  # Capture the start time
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
                "prompt_tokens": len(Params.input.split()),
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
        # Release the semaphore and calculate the processing time
        semaphore.release()
        end_time = time.time()  # Capture the end time
        processing_time = end_time - start_time
        # Calculate the number of used semaphore spots
        used_spots = int(os.getenv("API_CONCURRENCY", "16")) - semaphore._value
        print(
            f"Request processed in {processing_time:.2f} seconds, {used_spots} in queue"
        )
