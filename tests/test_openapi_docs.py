import importlib

from app import main


def test_openapi_includes_error_response_and_examples(monkeypatch):
    monkeypatch.setenv("EMBEDDING_ENDPOINT", "1")
    importlib.reload(main)
    openapi = main.app.openapi()

    assert openapi["openapi"] == "3.1.0"
    assert {t["name"] for t in openapi["tags"]} >= {"memory", "embedding"}

    scheme = openapi["components"]["securitySchemes"]["ApiKeyAuth"]
    assert scheme["type"] == "apiKey"
    assert scheme["name"] == "X-API-Key"
    assert scheme["in"] == "header"

    schemas = openapi["components"]["schemas"]
    assert "ErrorResponse" in schemas

    examples = schemas["ManageMemoryParams"]["examples"]
    actions = {ex["action"] for ex in examples}
    assert {"create", "delete", "forget"} <= actions

    embed_responses = openapi["paths"]["/embeddings"]["post"]["responses"]
    assert (
        embed_responses["403"]["content"]["application/json"]["schema"]["$ref"]
        .split("/")[-1]
        == "ErrorResponse"
    )
