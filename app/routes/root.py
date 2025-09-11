# routes/root.py
from pathlib import Path

from fastapi import APIRouter
from starlette.responses import FileResponse

# Create a new router for the root endpoints
root_router = APIRouter()


# Root endpoint - Serves the index.html file
@root_router.get("/", include_in_schema=False)
async def root() -> FileResponse:
    index_path = Path(__file__).resolve().parent.parent / "public" / "index.html"
    return FileResponse(index_path)
