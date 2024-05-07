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

# Semaphore to limit to the number of concurrent requests based on an environment variable
semaphore = asyncio.Semaphore(int(os.getenv("API_CONCURRENCY", "16")))

@embeddings_router.post("/v1/embeddings", operation_id="create_embedding")
async def embedding_request(Params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    start_time = time.time()  # Capture the start time
    try:
        # Acquire semaphore
        await semaphore.acquire()
        current_usage = int(os.getenv("API_CONCURRENCY", "16")) - semaphore._value  # Get current semaphore usage before processing
        print(f"Processing: {current_usage} embeddings requests")
        
        # First, await the completion of get_embeddings_model to get the model instance
        # model = await get_embeddings_model()
        # Run the blocking operation in a separate thread
        # embeddings_generator = await asyncio.to_thread(model.embed, Params.input)
        # vector = next(embeddings_generator)  # Assuming this part is quick and not blocking

        # Directly create a new instance instead of using the singleton
        model = TextEmbedding(os.getenv("LOCAL_MODEL"))
        embeddings_generator = await asyncio.to_thread(model.embed, Params.input)
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
        print(f"Processed an embeddin in {processing_time:.2f} seconds")
