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
    # Convert iterable to list to enable indexing
    vector_list = list(vector)
    if isinstance(vector_list[0], (list, tuple)):
        vector = vector_list[0]
    else:
        vector = vector_list
    vector_result = list(map(float, vector[0] if len(vector) == 1 else vector))
    return EmbeddingResponse(embedding=vector_result)
