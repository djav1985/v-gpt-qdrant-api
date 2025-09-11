import asyncio
from fastapi import APIRouter, Depends

from app.models import EmbeddingRequest, EmbeddingResponse
from app.dependencies import get_embeddings_model, get_api_key
from app.routes.common import ERROR_RESPONSES

router = APIRouter()


@router.post(
    "/embeddings",
    operation_id="create_embedding",
    dependencies=[Depends(get_api_key)],
    response_model=EmbeddingResponse,
    summary="Generate embeddings for text",
    description="Generate an embedding vector for the provided text.",
    tags=["embedding"],
    responses={
        200: {
            "model": EmbeddingResponse,
            "description": "Embedding vector",
        },
        **ERROR_RESPONSES,
    },
)
async def create_embedding(payload: EmbeddingRequest) -> EmbeddingResponse:
    """Generate an embedding vector for the provided text.

    Args:
        payload: Request data containing the text to embed.

    Returns:
        EmbeddingResponse: Vector representation of the input text.
    """
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, payload.text)
    vector = vector[0] if isinstance(vector[0], (list, tuple)) else vector
    vector_list = list(map(float, vector))
    return EmbeddingResponse(embedding=vector_list)
