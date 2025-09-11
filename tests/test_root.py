import os
from pathlib import Path

import pytest
from starlette.responses import FileResponse

from app.routes.root import root


def test_root_file_response_path():
    async def run():
        repo_root = Path(__file__).resolve().parents[1]
        old_cwd = Path.cwd()
        os.chdir(repo_root)
        try:
            response = await root()
        finally:
            os.chdir(old_cwd)
        assert isinstance(response, FileResponse)
        expected = repo_root / "app" / "public" / "index.html"
        assert Path(response.path) == expected

    import asyncio

    asyncio.run(run())
