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
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, payload.text)
    return EmbeddingResponse(embedding=vector.tolist())
