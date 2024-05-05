# Standard Library Imports
import os
from typing import List, Optional, Dict, Union

# Third-Party Library Imports
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastembed import TextEmbedding

# Local Imports
from models import EmbeddingParams
from dependencies import get_api_key, get_embeddings_model

embeddings_router = APIRouter()

# This is the endpoint that handles embedding requests
@embeddings_router.post("/v1/embeddings", operation_id="create_embedding")
async def embedding_request(params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    try:
        # Generate an embedding from the memory text using the AI model
        embeddings_generator = get_embeddings_model().embed(params.input)

        # Extract the single vector from the generator
        vector = next(embeddings_generator)  # This fetches the first item from the generator

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()  # Convert numpy array to list
        else:
            raise ValueError("The embedding is not in the expected format (np.ndarray)")  # Exception handling for unexpected formats

        # Construct the response data with usage details
        response_data = {
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": vector_list,
                "index": 0
            }],
            "model": params.model,
            "usage": {
                "prompt_tokens": len(params.input.split()),  # Count of tokens in the input prompt
                "total_tokens": len(vector_list)  # Count of tokens in the generated vector
            }
        }

        return response_data  # Return the response data
    except Exception as e:
        print(f"An error occurred: {e}")
        # Provide more detailed error messaging
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")  # Raise an exception if there's an error in processing the request
