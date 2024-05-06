# routes/embeddings.py
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
async def embedding_request(Params: EmbeddingParams, api_key: str = Depends(get_api_key)):
    try:
        # First, await the completion of get_embeddings_model to get the model instance
        model = await get_embeddings_model()

        # Then, use the model instance to call and await the embed method
        embeddings_generator = model.embed(Params.input)

        # Fetching the first item from the generator asynchronously
        vector = await embeddings_generator.__anext__()

        # Constructing the response data with usage details
        response_data = {
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": vector.tolist(),
                "index": 0
            }],
            "model": Params.model,
            "usage": {
                # Counting the tokens in the input prompt
                "prompt_tokens": len(Params.input.split()),
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
