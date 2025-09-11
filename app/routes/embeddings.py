import asyncio
from fastapi import APIRouter, Depends

from models import EmbeddingRequest, EmbeddingResponse, ErrorResponse
from dependencies import get_embeddings_model, get_api_key

router = APIRouter()

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    403: {"model": ErrorResponse, "description": "Forbidden"},
    404: {"model": ErrorResponse, "description": "Not Found"},
    422: {"model": ErrorResponse, "description": "Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}


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
