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

@embeddings_router.post("/embeddings", operation_id="create_embedding")
async def embedding_request(
    Params: EmbeddingParams, api_key: str = Depends(get_api_key)
):
    global current_embeddings
    start_time = time.time()  # Capture the start time
    current_embeddings += (
        1  # Increment the counter as we start processing a new request
    )
    print(f"Currently processing {current_embeddings} embeddings")

    try:
        model = get_embeddings_model()
        embeddings_generator = await asyncio.to_thread(model.embed, Params.input)
        vector = next(embeddings_generator)

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
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
    finally:
        end_time = time.time()
        processing_time = end_time - start_time
        current_embeddings -= 1  # Decrement the counter as we finish processing
        print(f"Finished an embedding in {processing_time:.2f} seconds.")
