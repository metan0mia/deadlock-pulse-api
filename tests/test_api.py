import uuid

import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_status(client):
    response = await client.get("/status")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "Deadlock Pulse API"
    assert "watches_total" in body


@pytest.mark.asyncio
async def test_register_login_and_watch(client):
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "securepass123"

    register = await client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201
    assert register.json()["email"] == email

    login = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    watch = await client.post(
        "/watches",
        headers=headers,
        json={"steam_id64": "76561198000000000", "label": "demo"},
    )
    assert watch.status_code == 201
    assert watch.json()["steam_id64"] == "76561198000000000"

    watches = await client.get("/watches", headers=headers)
    assert watches.status_code == 200
    assert len(watches.json()) == 1


@pytest.mark.asyncio
async def test_webhook_requires_auth(client):
    response = await client.get("/webhooks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analytics_raw_sql_empty(client):
    email = f"stats-{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "securepass123"})
    login = await client.post("/auth/login", data={"username": email, "password": "securepass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get("/analytics/heroes", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
