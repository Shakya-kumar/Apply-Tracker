def register(client, email="person@example.com", password="correct-horse-battery-staple"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def test_registration_creates_account_and_authenticated_tenant(client):
    response = register(client)
    assert response.status_code == 201
    token = response.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "person@example.com"
    assert me.json()["is_active"] is True


def test_duplicate_email_is_rejected(client):
    assert register(client).status_code == 201
    response = register(client, email="PERSON@example.com")
    assert response.status_code == 409


def test_login_and_logout_revoke_session(client):
    register(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_bad_credentials_and_missing_auth_are_rejected(client):
    register(client)
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401
