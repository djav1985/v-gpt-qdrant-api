import pytest
from starlette.responses import FileResponse

from routes.root import root


@pytest.mark.asyncio
async def test_root_file_response_path():
    response = await root()
    assert isinstance(response, FileResponse)
    assert response.path == "/app/public/index.html"
