"""
Unit & Integration Tests for Authentication and RBAC.
"""
import pytest
from app.core.security import create_access_token, decode_jwt_token, hash_password, verify_password


def test_password_hashing():
    raw_pass = "SecureEmergencyPass2026!"
    hashed = hash_password(raw_pass)
    assert verify_password(raw_pass, hashed)
    assert not verify_password("WrongPassword!", hashed)


def test_jwt_token_creation_and_decoding():
    token = create_access_token(subject="user-12345", role="officer", department_id="dept-99")
    payload = decode_jwt_token(token)
    assert payload["sub"] == "user-12345"
    assert payload["role"] == "officer"
    assert payload["department_id"] == "dept-99"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_api_register_and_login(client):
    reg_data = {
        "name": "Integration Test Citizen",
        "email": "int_citizen@test.org",
        "password": "Password123!",
        "role": "citizen",
    }
    r = await client.post("/api/v1/auth/register", json=reg_data)
    assert r.status_code in [201, 400]  # 400 if already created

    login_data = {
        "email": "int_citizen@test.org",
        "password": "Password123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_data)
    assert login_res.status_code == 200
    res_json = login_res.json()
    assert "access_token" in res_json
    assert res_json["role"] == "citizen"

    # Test /auth/me with bearer
    token = res_json["access_token"]
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "int_citizen@test.org"
