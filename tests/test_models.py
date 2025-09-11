import pytest
from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError

from app.models import (
    SaveParams,
    SearchParams,
    ManageMemoryParams,
    SaveMemoryResponse,
    RecallMemoryResponse,
    ManageMemoryResponse,
    MemoryRecord,
    EmbeddingRequest,
    EmbeddingResponse,
    ErrorResponse,
)


def test_saveparams_lists_unchanged():
    params = SaveParams(
        memory_bank="bank",
        memory="hello",
        sentiment="neutral",
        entities=["a", "b"],
        tags=["x", "y"],
    )
    assert params.entities == ["a", "b"]
    assert params.tags == ["x", "y"]


def test_save_params_splits_comma_separated_fields():
    params = SaveParams(
        memory_bank="bank1",
        memory="a memory",
        sentiment="positive",
        entities="alice, bob",
        tags="tag1, tag2",
    )
    assert params.entities == ["alice", "bob"]
    assert params.tags == ["tag1", "tag2"]


def test_models_reject_extra_fields():
    with pytest.raises(ValidationError):
        SaveParams(
            memory_bank="bank",
            memory="hello",
            sentiment="neutral",
            entities=["a"],
            tags=["t"],
            extra="x",
        )
    with pytest.raises(ValidationError):
        SearchParams(memory_bank="bank", query="q", unknown=1)


def test_save_params_rejects_invalid_memory_bank():
    with pytest.raises(ValidationError):
        SaveParams(
            memory_bank="invalid bank",
            memory="mem",
            sentiment="neutral",
            entities=[],
            tags=[],
        )


def test_search_params_top_k_limits():
    with pytest.raises(ValidationError):
        SearchParams(memory_bank="bank", query="q", top_k=0)
    SearchParams(memory_bank="bank", query="q", top_k=1)
    SearchParams(memory_bank="bank", query="q", top_k=100)
    with pytest.raises(ValidationError):
        SearchParams(memory_bank="bank", query="q", top_k=101)


def test_manage_memory_params_invalid_memory_bank():
    with pytest.raises(ValidationError):
        ManageMemoryParams(memory_bank="invalid-bank", action="create")


def test_search_params_rejects_invalid_memory_bank():
    with pytest.raises(ValidationError):
        SearchParams(memory_bank="invalid bank", query="q")


def test_manage_memory_params_uuid_rules():
    valid_uuid = uuid4()
    # uuid required for forget
    with pytest.raises(ValidationError):
        ManageMemoryParams(memory_bank="bank", action="forget")
    # uuid must be valid
    with pytest.raises(ValidationError):
        ManageMemoryParams(
            memory_bank="bank",
            action="forget",
            uuid="not-a-uuid",
        )
    # uuid allowed only for forget
    with pytest.raises(ValidationError):
        ManageMemoryParams(
            memory_bank="bank",
            action="create",
            uuid=valid_uuid,
        )
    # valid cases
    ManageMemoryParams(
        memory_bank="bank",
        action="forget",
        uuid=valid_uuid,
    )
    ManageMemoryParams(memory_bank="bank", action="create")


def test_blank_strings_rejected():
    with pytest.raises(ValidationError):
        SaveParams(
            memory_bank="bank",
            memory="   ",
            sentiment="neutral",
            entities=[],
            tags=[],
        )
    with pytest.raises(ValidationError):
        SearchParams(memory_bank="bank", query="   ")


def test_sentiment_enum_enforced():
    with pytest.raises(ValidationError):
        SaveParams(
            memory_bank="bank",
            memory="m",
            sentiment="bad",
            entities=[],
            tags=[],
        )
    with pytest.raises(ValidationError):
        SearchParams(memory_bank="bank", query="q", sentiment="bad")
    with pytest.raises(ValidationError):
        MemoryRecord(
            id=uuid4(),
            memory="m",
            timestamp=datetime.utcnow(),
            sentiment="bad",
            entities=[],
            tags=[],
            score=0.5,
        )


def test_memoryrecord_type_enforcement():
    with pytest.raises(ValidationError):
        MemoryRecord(
            id="not-uuid",
            memory="m",
            timestamp=datetime.utcnow(),
            sentiment="neutral",
            entities=[],
            tags=[],
            score=0.5,
        )
    with pytest.raises(ValidationError):
        MemoryRecord(
            id=uuid4(),
            memory="m",
            timestamp="not-a-date",
            sentiment="neutral",
            entities=[],
            tags=[],
            score=0.5,
        )
    with pytest.raises(ValidationError):
        MemoryRecord(
            id=uuid4(),
            memory="m",
            timestamp=datetime.utcnow(),
            sentiment="neutral",
            entities=[],
            tags=[],
            score=1.5,
        )
    with pytest.raises(ValidationError):
        MemoryRecord(
            id=uuid4(),
            memory="m",
            timestamp=datetime.utcnow(),
            sentiment="neutral",
            entities=[],
            tags=[],
            score=-0.1,
        )


def test_response_models():
    save_resp = SaveMemoryResponse(message="ok")
    assert save_resp.message == "ok"

    item_id = uuid4()
    item = MemoryRecord(
        id=item_id,
        memory="m",
        timestamp=datetime(2024, 1, 1, 0, 0, 0),
        sentiment="neutral",
        entities=["a"],
        tags=["t"],
        score=0.1,
    )
    recall_resp = RecallMemoryResponse(results=[item])
    assert recall_resp.results[0].id == item_id

    manage_resp = ManageMemoryResponse(message="done")
    assert manage_resp.message == "done"


def test_embedding_models_and_error_response():
    req = EmbeddingRequest(text="hello")
    assert req.text == "hello"
    resp = EmbeddingResponse(embedding=[0.1, 0.2])
    assert resp.embedding == [0.1, 0.2]
    err = ErrorResponse(status=400, code="bad_request", detail="oops")
    assert err.status == 400
    assert err.code == "bad_request"
    assert err.detail == "oops"
