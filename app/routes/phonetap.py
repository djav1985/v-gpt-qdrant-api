import os
import uuid
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, VectorParams
from models import InputParams, OutputParams, ModerationRequest
from dependencies import get_api_key, get_embeddings_model, create_qdrant_client

# Creating an instance of the FastAPI router
phonetap_router = APIRouter()

@phonetap_router.post("/phonetap/{memory_bank}", operation_id="phonetap")
async def phonetap(
    memory_bank: str,
    moderation_request: ModerationRequest,
    api_key: str = Depends(get_api_key),
    db_client: AsyncQdrantClient = Depends(create_qdrant_client),
):
    try:
        # Handle point cases
        if moderation_request.point == "ping":
            await db_client.create_collection(
                collection_name=memory_bank,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),  # Configure vector parameters
            )
            await db_client.create_payload_index(
                collection_name=memory_bank,
                field_name="speaker", field_schema="keyword"
            )
            return {"point": "pong"}

        # Handle input moderation
        elif moderation_request.point == "app.moderation.input":
            params = InputParams(**moderation_request.params)
            try:
                # Get model and generate embeddings
                model = get_embeddings_model()
                embeddings_generator = await asyncio.to_thread(model.embed, params.query)
                vector = next(embeddings_generator)

                # Create unique id and timestamp
                timestamp = datetime.utcnow().isoformat()
                unique_id = str(uuid.uuid4())

                # Save memory in Qdrant
                await db_client.upsert(
                    collection_name=memory_bank,
                    points=[
                        models.PointStruct(
                            id=unique_id,
                            payload={
                                "message": params.query,
                                "timestamp": timestamp,
                                "role": "User",
                            },
                            vector=vector.tolist(),
                        ),
                    ],
                )
                return {
                    "flagged": False,
                    "action": "direct_output",
                    "inputs": params.inputs,
                    "query": params.query
                }

            except Exception as e:
                print(f"An error occurred: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Error processing request: {str(e)}"
                )

        # Handle output moderation
        elif moderation_request.point == "app.moderation.output":
            params = OutputParams(**moderation_request.params)
            try:
                # Get model and generate embeddings
                model = get_embeddings_model()
                embeddings_generator = await asyncio.to_thread(model.embed, params.text)
                vector = next(embeddings_generator)

                # Create unique id and timestamp
                timestamp = datetime.utcnow().isoformat()
                unique_id = str(uuid.uuid4())

                # Save memory in Qdrant
                await db_client.upsert(
                    collection_name=memory_bank,
                    points=[
                        models.PointStruct(
                            id=unique_id,
                            payload={
                                "message": params.text,
                                "timestamp": timestamp,
                                "role": "Assistant",
                            },
                            vector=vector.tolist(),
                        ),
                    ],
                )
                return {
                    "flagged": False,
                    "action": "direct_output",
                    "text": params.text
                }

            except Exception as e:
                print(f"An error occurred: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Error processing request: {str(e)}"
                )

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
