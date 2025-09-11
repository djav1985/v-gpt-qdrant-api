from fastapi import FastAPI

from routes.memory import memory_router
from routes.embeddings import embeddings_router


def test_openapi_includes_error_response_and_examples():
    app = FastAPI()
    app.include_router(memory_router)
    app.include_router(embeddings_router)
    openapi = app.openapi()

    schemas = openapi["components"]["schemas"]
    assert "ErrorResponse" in schemas

    examples = schemas["ManageMemoryParams"]["examples"]
    actions = {ex["action"] for ex in examples}
    assert {"create", "delete", "forget"} <= actions

    save_responses = openapi["paths"]["/save_memory"]["post"]["responses"]
    assert (
        save_responses["400"]["content"]["application/json"]["schema"]["$ref"]
        .split("/")[-1]
        == "ErrorResponse"
    )

    embed_responses = openapi["paths"]["/embeddings"]["post"]["responses"]
    assert (
        embed_responses["403"]["content"]["application/json"]["schema"]["$ref"]
        .split("/")[-1]
        == "ErrorResponse"
    )
