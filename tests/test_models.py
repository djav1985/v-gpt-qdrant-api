import pytest
from pydantic import ValidationError

from app.models import SaveParams, SearchParams, ManageMemoryParams


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
