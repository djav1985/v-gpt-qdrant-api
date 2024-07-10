# /routes/manage

# Importing standard libraries for operating system interaction and async functionality
import os
from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import (
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    PointStruct,
)

from models import ManageMemoryParams
from dependencies import get_api_key, create_qdrant_client

manage_router = APIRouter()


# Endpoint to manage memories
@memory_router.post("/manage_memories", operation_id="manage_memories")
async def manage_memories(
    Params: ManageMemoryParams,
    api_key: str = Depends(get_api_key),
    Qdrant: AsyncQdrantClient = Depends(create_qdrant_client),
):
    try:
        if Params.action == "create":
            # Create new memory bank in Qdrant
            await Qdrant.create_collection(
                collection_name=Params.memory_bank,
                vectors_config=VectorParams(
                    size=int(os.getenv("DIM")), distance=Distance.COSINE
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=False,
                    ),
                ),
            )

            # Create payload index for each field in the newly created collection
            index_fields = ["sentiment", "entities", "tags"]
            for field in index_fields:
                await Qdrant.create_payload_index(
                    collection_name=Params.memory_bank,
                    field_name=field,
                    field_schema="keyword",
                )

            return {
                "message": f"Memory Bank '{Params.memory_bank}' created successfully"
            }

        elif Params.action == "delete":
            # Delete entire memory bank
            await Qdrant.delete_collection(collection_name=Params.memory_bank)

            return {"message": f"Memory Bank '{Params.memory_bank}' has been deleted."}

        elif Params.action == "forget":
            if Params.uuid is None:
                raise HTTPException(
                    status_code=400, detail="UUID must be provided for forget action"
                )

            # Delete specific memory using UUID
            await Qdrant.delete(
                collection_name=Params.memory_bank, points_selector=[Params.uuid]
            )

            return {
                "message": f"Memory with UUID '{Params.uuid}' has been forgotten from Memory Bank '{Params.memory_bank}'."
            }

    except Exception as e:
        # Log and raise an exception if an error occurs
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
