# routes/root.py
from fastapi import APIRouter
from starlette.responses import FileResponse

# Create a new router for the root endpoints
root_router = APIRouter()


# Root endpoint - Serves the index.html file
@root_router.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")


# v1 endpoint - Serves the index.html file
@root_router.get("/v1", include_in_schema=False)
async def v1():
    return FileResponse("/app/public/index.html")
