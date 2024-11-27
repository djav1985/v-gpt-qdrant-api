# /routes/phonetap.py
from fastapi import APIRouter, Depends, HTTPException

from qdrant_client import AsyncQdrantClient

from models import ModerationRequest
from dependencies import get_api_key, create_qdrant_client

# Creating an instance of the FastAPI router
phonetap_router = APIRouter()

# Endpoint to handle phone-tap functionality
@phonetap_router.post("/phone-tap/{user_id}", operation_id="phone-tap")
async def phone_tap(
    moderation_request: ModerationRequest,
    user_id: str,  # Add user_id as a path parameter
    api_key: str = Depends(get_api_key),
    db_client: AsyncQdrantClient = Depends(create_qdrant_client),
):
    try:
        # Handle "ping" point requests
        if moderation_request.point == "ping":
            # Check if the collection exists in Qdrant
            #await db_client.get_collection(collection_name="shortterm")
            return {"point": "pong"}

        # Handle output moderation requests
        elif moderation_request.point == "app.moderation.output":
            # Correct the key to 'text' for output moderation
            text = moderation_request.params.get("text", "No output provided")
            # You could also perform some operation here if needed
            # await record_memory(user_id, text)

            # Only return 'flagged' status for output moderation
            return {"flagged": False}  # No flagging, just return False

        # Handle input moderation requests
        elif moderation_request.point == "app.moderation.input":
            # Parse the input parameters directly from the moderation request's params dictionary
            query = moderation_request.params.get("query", "No query provided")
            
            # You could also perform some operation here if needed
            # await record_memory(user_id, query)

            # Only return 'flagged' status for input moderation
            return {"flagged": False}  # No flagging, just return False

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid point specified. Must be 'ping', 'app.moderation.output', or 'app.moderation.input'."
            )

    except HTTPException as http_exc:
        # Log and raise an exception if an HTTP error occurs during request handling
        print(f"HTTP error occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Log and raise an exception if an error occurs during request handling
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
