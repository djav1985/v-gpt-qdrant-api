from models import SaveParams


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
