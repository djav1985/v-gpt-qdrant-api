import os
import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams

from models import (
    SaveParams,
    SearchParams,
    ManageMemoryParams,
    SaveMemoryResponse,
    RecallMemoryResponse,
    ManageMemoryResponse,
    MemoryRecord,
    ErrorResponse,
)
from dependencies import (
    get_embeddings_model,
    create_qdrant_client,
    get_api_key,
)

memory_router = APIRouter()


# --- Save Memory ---
@memory_router.post(
    "/save_memory",
    operation_id="save_memory",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=60)),
        Depends(get_api_key),
    ],
    response_model=SaveMemoryResponse,
    summary="Save a memory",
    description="Store a memory with sentiment, entities, and tags in a memory bank.",  # noqa: E501
    tags=["memory"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Memory content cannot be empty",
            "content": {
                "application/json": {
                    "example": {"detail": "Memory content cannot be empty"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Invalid API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            },
        },
    },
)
async def save_memory(
    params: SaveParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> SaveMemoryResponse:
    if not params.memory.strip():
        raise HTTPException(
            status_code=400,
            detail="Memory content cannot be empty",
        )

    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.memory)
    uuid_str = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    await qdrant.upsert(
        collection_name=params.memory_bank,
        points=[
            models.PointStruct(
                id=uuid_str,
                vector=vector.tolist(),
                payload={
                    "memory": params.memory,
                    "timestamp": timestamp,
                    "sentiment": params.sentiment,
                    "entities": params.entities,
                    "tags": params.tags,
                },
            )
        ],
    )
    return SaveMemoryResponse(message="Memory saved successfully")


# --- Recall Memory ---
@memory_router.post(
    "/recall_memory",
    operation_id="recall_memory",
    dependencies=[
        Depends(RateLimiter(times=10, seconds=60)),
        Depends(get_api_key),
    ],
    response_model=RecallMemoryResponse,
    summary="Recall memories",
    description="Retrieve memories similar to a query from a memory bank.",
    tags=["memory"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid memory bank name or blank query",
            "content": {
                "application/json": {
                    "example": {"detail": "query cannot be blank"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Invalid API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            },
        },
    },
)
async def recall_memory(
    params: SearchParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> RecallMemoryResponse:
    model = get_embeddings_model()
    vector = await asyncio.to_thread(model.embed, params.query)

    filters = []
    if params.entity:
        filters.append(
            models.FieldCondition(
                key="entities", match=models.MatchValue(value=params.entity)
            )
        )
    if params.sentiment:
        filters.append(
            models.FieldCondition(
                key="sentiment", match=models.MatchAny(any=[params.sentiment])
            )
        )
    if params.tag:
        filters.append(
            models.FieldCondition(
                key="tags",
                match=models.MatchAny(any=[params.tag]),
            )
        )

    hits = await qdrant.search(
        collection_name=params.memory_bank,
        query_vector=vector.tolist(),
        query_filter=models.Filter(must=filters) if filters else None,
        with_payload=True,
        limit=params.top_k,
    )
    return RecallMemoryResponse(
        results=[
            MemoryRecord(
                id=hit.id,
                memory=hit.payload["memory"],
                timestamp=hit.payload["timestamp"],
                sentiment=hit.payload["sentiment"],
                entities=hit.payload["entities"],
                tags=hit.payload["tags"],
                score=hit.score,
            )
            for hit in hits
        ]
    )


# --- Manage Memories ---
@memory_router.post(
    "/manage_memories",
    operation_id="manage_memories",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=60)),
        Depends(get_api_key),
    ],
    response_model=ManageMemoryResponse,
    summary="Manage memory banks",
    description=(
        "Create, delete, or forget memories within a memory bank.\n\n"
        "**Create**\n"
        "Request:\n"
        "```json\n{\"memory_bank\": \"personal_bank\", \"action\": \"create\"}\n```\n"
        "Response:\n"
        "```json\n{\"message\": \"Memory Bank 'personal_bank' created successfully\"}\n```\n"
        "**Delete**\n"
        "Request:\n"
        "```json\n{\"memory_bank\": \"personal_bank\", \"action\": \"delete\"}\n```\n"
        "Response:\n"
        "```json\n{\"message\": \"Memory Bank 'personal_bank' has been deleted.\"}\n```\n"
        "**Forget**\n"
        "Request:\n"
        "```json\n"
        "{\"memory_bank\": \"personal_bank\", \"action\": \"forget\", "
        "\"uuid\": \"123e4567-e89b-12d3-a456-426614174000\"}\n```\n"
        "Response:\n"
        "```json\n"
        "{\"message\": \"Memory with UUID '123e4567-e89b-12d3-a456-426614174000' "
        "has been forgotten from Memory Bank 'personal_bank'.\"}\n```"
    ),
    tags=["memory"],
    responses={
        200: {
            "description": "Successful memory management response",
            "content": {
                "application/json": {
                    "examples": {
                        "create": {
                            "summary": "Create memory bank",
                            "value": {
                                "message": "Memory Bank 'personal_bank' created successfully"
                            },
                        },
                        "delete": {
                            "summary": "Delete memory bank",
                            "value": {
                                "message": "Memory Bank 'personal_bank' has been deleted."
                            },
                        },
                        "forget": {
                            "summary": "Forget memory",
                            "value": {
                                "message": (
                                    "Memory with UUID '123e4567-e89b-12d3-a456-426614174000' "
                                    "has been forgotten from Memory Bank 'personal_bank'."
                                )
                            },
                        },
                    }
                }
            },
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid memory bank name or missing UUID",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid memory bank name or missing UUID"
                    }
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Invalid API key",
            "content": {
                "application/json": {"example": {"detail": "Invalid API key"}}
            },
        },
    },
)
async def manage_memories(
    params: ManageMemoryParams,
    qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
) -> ManageMemoryResponse:
    if not params.memory_bank.isidentifier():
        raise HTTPException(status_code=400, detail="Invalid memory bank name")

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
                detail="UUID must be provided for forget action",  # noqa: E501
            )
        await qdrant.delete(
            collection_name=params.memory_bank,
            points_selector=models.PointIdsList(points=[str(params.uuid)]),
        )
        return ManageMemoryResponse(
            message=(
                f"Memory with UUID '{params.uuid}' has been forgotten from Memory Bank"  # noqa: E501
                f" '{params.memory_bank}'."
            )
        )
