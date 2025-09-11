import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams

from models import (
    ManageMemoryParams,
    ManageMemoryResponse,
    ErrorResponse,
)
from dependencies import create_qdrant_client, get_api_key

router = APIRouter()
rate_limiter = RateLimiter(times=5, seconds=60)

RATE_LIMIT_HEADERS = {
    "X-RateLimit-Limit": {"$ref": "#/components/headers/X-RateLimit-Limit"},
    "X-RateLimit-Remaining": {"$ref": "#/components/headers/X-RateLimit-Remaining"},
    "X-RateLimit-Reset": {"$ref": "#/components/headers/X-RateLimit-Reset"},
}

ERROR_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "Bad Request",
        "headers": RATE_LIMIT_HEADERS,
    },
    401: {
        "model": ErrorResponse,
        "description": "Unauthorized",
        "headers": RATE_LIMIT_HEADERS,
    },
    403: {
        "model": ErrorResponse,
        "description": "Forbidden",
        "headers": RATE_LIMIT_HEADERS,
    },
    404: {
        "model": ErrorResponse,
        "description": "Not Found",
        "headers": RATE_LIMIT_HEADERS,
    },
    422: {
        "model": ErrorResponse,
        "description": "Validation Error",
        "headers": RATE_LIMIT_HEADERS,
    },
    429: {
        "model": ErrorResponse,
        "description": "Too Many Requests",
        "headers": RATE_LIMIT_HEADERS,
    },
    500: {
        "model": ErrorResponse,
        "description": "Internal Server Error",
        "headers": RATE_LIMIT_HEADERS,
    },
}


@router.post(
    "/manage_memories",
    operation_id="manage_memories",
    dependencies=[Depends(rate_limiter), Depends(get_api_key)],
    response_model=ManageMemoryResponse,
    summary="Manage memory banks",
    description=(
        "Create, delete, or forget memories within a memory bank.\n\n"
        "**Create**\nRequest:\n``{\"memory_bank\": \"personal_bank\", \"action\": \"create\"}``"
        "\n**Delete**\nRequest:\n``{\"memory_bank\": \"personal_bank\", \"action\": \"delete\"}``"
        "\n**Forget**\nRequest:\n``{\"memory_bank\": \"personal_bank\", \"action\": \"forget\", \"uuid\": \"123e4567-e89b-12d3-a456-426614174000\"}``"
    ),
    tags=["memory"],
    responses={
        200: {
            "model": ManageMemoryResponse,
            "description": "Successful memory management response",
            "headers": RATE_LIMIT_HEADERS,
        },
        **ERROR_RESPONSES,
    },
)
async def manage_memories(
    params: ManageMemoryParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> ManageMemoryResponse:
    if not params.memory_bank.isidentifier():
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                status=400,
                code="invalid_memory_bank",
                detail="Invalid memory bank name",
            ).model_dump(),
        )

    if params.action == "create":
        await asyncio.gather(
            qdrant.create_collection(
                collection_name=params.memory_bank,
                vectors_config=VectorParams(
                    size=int(os.getenv("DIM")),
                    distance=Distance.COSINE,
                ),
            ),
            *[
                qdrant.create_payload_index(
                    collection_name=params.memory_bank,
                    field_name=field,
                    field_schema="keyword",
                )
                for field in ["sentiment", "entities", "tags"]
            ],
        )
        return ManageMemoryResponse(
            message=f"Memory Bank '{params.memory_bank}' created successfully"
        )

    elif params.action == "delete":
        await qdrant.delete_collection(collection_name=params.memory_bank)
        return ManageMemoryResponse(
            message=f"Memory Bank '{params.memory_bank}' has been deleted."
        )

    elif params.action == "forget":
        if not params.uuid:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    status=400,
                    code="missing_uuid",
                    detail="UUID must be provided for forget action",
                ).model_dump(),
            )
        await qdrant.delete(
            collection_name=params.memory_bank,
            points_selector=models.PointIdsList(points=[str(params.uuid)]),
        )
        return ManageMemoryResponse(
            message=(
                f"Memory with UUID '{params.uuid}' has been forgotten from Memory Bank '{params.memory_bank}'."
            )
        )
