from fastapi import FastAPI, HTTPException
from fastembed import TextEmbedding
from pydantic import BaseModel

app = FastAPI()

# Initialize the embeddings model
embeddings_model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

class EmbeddingResponse(BaseModel):
    object: str
    data: list
    model: str
    usage: dict

@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    # Generate embeddings
    try:
        embeddings = embeddings_model.embed([request.input])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

    # Prepare the response data
    response_data = [{
        "object": "embedding",
        "index": 0,
        "embedding": embeddings[0].tolist()  # Assuming the model returns a list of embeddings
    }]

    # Example usage information, adjust according to your actual usage metrics
    usage_info = {
        "prompt_tokens": len(request.input.split()),  # Example of counting tokens
        "total_tokens": len(request.input.split())
    }

    return EmbeddingResponse(
        object="list",
        data=response_data,
        model="nomic-ai/nomic-embed-text-v1.5",
        usage=usage_info
    )
