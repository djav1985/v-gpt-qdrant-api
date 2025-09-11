from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.dependencies import initialize_text_embedding
from app.config import get_settings
from app.routes.save_memory import router as save_memory_router  # noqa: E402
from app.routes.recall_memory import router as recall_memory_router  # noqa: E402
from app.routes.manage_memories import (  # noqa: E402
    router as manage_memories_router,
)
from app.routes.root import root_router  # noqa: E402

tags_metadata = [
    {
        "name": "memory",
        "description": "Operations related to memory management.",
    },
    {
        "name": "embedding",
        "description": "Endpoints for generating embeddings.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from pydantic import ValidationError

    try:
        settings = get_settings()
    except ValidationError as exc:
        for err in exc.errors():
            if err["loc"] == ("DIM",):
                raise RuntimeError("DIM must be an integer") from exc
        raise RuntimeError(str(exc)) from exc

    app.state.dim = settings.DIM
    app.state.settings = settings
    await initialize_text_embedding()
    yield


_settings = get_settings()
app = FastAPI(
    title="AI Memory API",
    version="0.1.0",
    description="A FastAPI application that allows users to save memories ...",
    openapi_tags=tags_metadata,
    root_path=_settings.ROOT_PATH,
    root_path_in_servers=False,
    servers=[
        {
            "url": f"{_settings.BASE_URL}{_settings.ROOT_PATH}",
            "description": "Base API server",
        }
    ],
    lifespan=lifespan,
)

app.include_router(save_memory_router)
app.include_router(recall_memory_router)
app.include_router(manage_memories_router)

if _settings.EMBEDDING_ENDPOINT:
    from app.routes.embeddings import router as embeddings_router

    app.include_router(embeddings_router)

app.include_router(root_router)


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )
    openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )["ApiKeyAuth"] = {
        "type": "apiKey",
        "name": "X-API-Key",
        "in": "header",
    }
    openapi_schema["openapi"] = "3.1.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}
    )
