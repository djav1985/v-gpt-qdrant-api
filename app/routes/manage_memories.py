import asyncio
from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams

from app.config import get_settings
from app.models import ActionEnum, ManageMemoryParams, ManageMemoryResponse, ErrorResponse
from app.dependencies import create_qdrant_client, get_api_key
from app.routes.common import ERROR_RESPONSES

router = APIRouter()


@router.post(
    "/manage_memories",
    operation_id="manage_memories",
    dependencies=[Depends(get_api_key)],
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
        },
        **ERROR_RESPONSES,
    },
)
async def manage_memories(
    params: ManageMemoryParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> ManageMemoryResponse:
    """Create, delete, or forget memories within a memory bank.

    Args:
        params: Memory bank action and related parameters.
        qdrant: Async Qdrant client dependency.

    Returns:
        ManageMemoryResponse: Result of the management action.
    """
    if params.action is ActionEnum.CREATE:
        await asyncio.gather(
            qdrant.create_collection(
                collection_name=params.memory_bank,
                vectors_config=VectorParams(
                    size=get_settings().DIM,
                    distance=Distance.COSINE,
                ),
            ),
            *[
            qdrant.create_payload_index(
                collection_name=params.memory_bank,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            for field in ["sentiment", "entities", "tags"]
        ],
        )
        return ManageMemoryResponse(
            message=f"Memory Bank '{params.memory_bank}' created successfully"
        )

    elif params.action is ActionEnum.DELETE:
        await qdrant.delete_collection(collection_name=params.memory_bank)
        return ManageMemoryResponse(
            message=f"Memory Bank '{params.memory_bank}' has been deleted."
        )

    elif params.action is ActionEnum.FORGET:
        await qdrant.delete(
            collection_name=params.memory_bank,
            points_selector=models.PointIdsList(points=[str(params.uuid)]),
        )
        return ManageMemoryResponse(
            message=(
                f"Memory with UUID '{params.uuid}' has been forgotten from Memory Bank '{params.memory_bank}'."
            )
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                status=400,
                code="invalid_action",
                detail=f"Unsupported action: {params.action}",
            ).model_dump(),
        )
