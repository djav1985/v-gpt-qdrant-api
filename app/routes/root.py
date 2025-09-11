# routes/root.py
from pathlib import Path

from fastapi import APIRouter
from starlette.responses import FileResponse

# Create a new router for the root endpoints
root_router = APIRouter()


INDEX_PATH = Path(__file__).resolve().parents[1] / "public" / "index.html"


# Root endpoint - Serves the index.html file
@root_router.get("/", include_in_schema=False)
async def root():
    return FileResponse(INDEX_PATH)


# v1 endpoint - Serves the index.html file
@root_router.get("/v1", include_in_schema=False)
async def v1():
    return FileResponse(INDEX_PATH)
