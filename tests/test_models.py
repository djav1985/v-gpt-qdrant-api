import pytest
from pydantic import ValidationError

from models import (
    SaveParams,
    SearchParams,
    ManageMemoryParams,
    SaveMemoryResponse,
    RecallMemoryResponse,
    ManageMemoryResponse,
    MemoryRecord,
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


def test_response_models():
    save_resp = SaveMemoryResponse(message="ok")
    assert save_resp.message == "ok"

    item = MemoryRecord(
        id="1",
        memory="m",
        timestamp="2024-01-01T00:00:00Z",
        sentiment="neutral",
        entities=["a"],
        tags=["t"],
        score=0.1,
    )
    recall_resp = RecallMemoryResponse(results=[item])
    assert recall_resp.results[0].id == "1"

    manage_resp = ManageMemoryResponse(message="done")
    assert manage_resp.message == "done"
