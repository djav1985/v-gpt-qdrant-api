# /routes/root.py

# Import necessary classes from FastAPI and Starlette libraries
from fastapi import APIRouter
from starlette.responses import FileResponse

# Create a new router object for defining the root endpoints
root_router = APIRouter()


# Endpoint to serve favicon.ico file
@root_router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Return the favicon.ico file located in the /app/public directory
    return FileResponse("/app/public/favicon.ico")


# Catch-all endpoint to serve index.html for any unspecified routes
@root_router.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    # Return the index.html file located in the /app/public directory
    return FileResponse("/app/public/index.html")
