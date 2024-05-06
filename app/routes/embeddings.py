# routes/embeddings.py

# Importing necessary libraries and modules
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastembed import TextEmbedding

# Local Imports
from models import EmbeddingParams
from dependencies import get_api_key, get_embeddings_model

# Creating an instance of the FastAPI router
embeddings_router = APIRouter()

# This is the endpoint that handles embedding requests
@embeddings_router.post("/v1/embeddings", operation_id="create_embedding")
# The function below creates an embedding for the given input text.
async def embedding_request(params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    try:
        # Extracting the single vector from the generator
        embeddings_model = await get_embeddings_model()
        embeddings_generator = embeddings_model.embed(params.input)

        # Fetching the first item from the generator
        vector = next(embeddings_generator)

        # Converting the vector to a list
        vector_list = vector.tolist()

        # Constructing the response data with usage details
        response_data = {
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": vector_list,
                "index": 0
            }],
            "model": params.model,
            "usage": {
                # Counting the tokens in the input prompt
                "prompt_tokens": len(params.input.split()),
                # Counting the tokens in the generated vector
                "total_tokens": len(vector_list)
            }
        }

        # Returning the response data
        return response_data
    except Exception as e:
        print(f"An error occurred: {e}")
        # Raising an exception if there's an error in processing the request
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
