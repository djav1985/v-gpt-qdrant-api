# ;routes/embeddings.py

# Importing standard libraries for operating system interaction and async functionality
import os
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException

from fastembed import TextEmbedding
from models import EmbeddingParams
from dependencies import get_api_key, get_embeddings_model

# Creating an instance of the FastAPI router
embeddings_router = APIRouter()

# Global counter for tracking concurrent embeddings
current_embeddings = 0


# Endpoint to handle embedding creation requests
@embeddings_router.post("/embeddings", operation_id="create-embedding")
async def embedding_request(
    Params: EmbeddingParams, api_key: str = Depends(get_api_key)
):
    global current_embeddings
    start_time = time.time()  # Capture the start time of the request

    # Increment the counter as we start processing a new request
    current_embeddings += 1
    print(f"Currently processing {current_embeddings} embeddings")

    try:
        # Get the embeddings model
        model = get_embeddings_model()

        # Generate embeddings asynchronously
        embeddings_generator = await asyncio.to_thread(model.embed, Params.input)
        vector = next(embeddings_generator)

        # Prepare the response data
        response_data = {
            "object": "list",
            "data": [{"object": "embedding", "embedding": vector.tolist(), "index": 0}],
            "model": os.getenv("LOCAL_MODEL"),
            "usage": {
                "prompt_tokens": len(Params.input.split()),
                "total_tokens": len(vector.tolist()),
            },
        }
        return response_data

    except Exception as e:
        # Log and raise an exception if an error occurs during request handling
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )

    finally:
        # Capture the end time and calculate the processing time
        end_time = time.time()
        processing_time = end_time - start_time

        # Decrement the counter as we finish processing the request
        current_embeddings -= 1
        print(f"Finished an embedding in {processing_time:.2f} seconds.")
