import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-32chars")
os.environ.setdefault("ENABLE_POLLER", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import engine, init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    await init_db()
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
