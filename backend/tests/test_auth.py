async def register(client, email="sai@example.com", password="password123"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Sai", "password": password, "skills": ["python"]},
    )


async def login(client, email="sai@example.com", password="password123"):
    return await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


async def test_register_success(client):
    r = await register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "sai@example.com"
    assert "password" not in body and "hashed_password" not in body


async def test_register_duplicate_email(client):
    await register(client)
    r = await register(client)
    assert r.status_code == 409


async def test_register_short_password(client):
    r = await register(client, password="short")
    assert r.status_code == 422


async def test_login_success(client):
    await register(client)
    r = await login(client)
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await register(client)
    r = await login(client, password="wrongpassword")
    assert r.status_code == 401


async def test_me_requires_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)  # FastAPI 0.115 returns 403 for a missing header


async def test_me_with_token(client):
    await register(client)
    token = (await login(client)).json()["access_token"]
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "sai@example.com"