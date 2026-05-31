import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-32chars")
os.environ.setdefault("ENABLE_POLLER", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import init_db
from app.main import app


@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
