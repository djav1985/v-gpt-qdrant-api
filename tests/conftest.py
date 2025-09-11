import sys
from pathlib import Path
import types

# Ensure project root is importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Stub fastembed to avoid heavy dependency during tests
fastembed_stub = types.ModuleType("fastembed")


class _DummyTextEmbedding:
    def __init__(self, *args, **kwargs):
        pass

    def embed(self, text: str):  # pragma: no cover - simple stub
        return [0.0]


fastembed_stub.TextEmbedding = _DummyTextEmbedding
sys.modules["fastembed"] = fastembed_stub
