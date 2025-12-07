import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_ping():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        resp = await ac.get('/ping')

    assert resp.status_code == 200
    assert resp.json() == {'ping': 'pong'}
