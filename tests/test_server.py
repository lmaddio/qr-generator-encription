import pytest
from fastapi.testclient import TestClient
import json
# Server tests with TestClient (no src edit)

from qr_cli.server import app

client = TestClient(app)

def test_get_qr_simple():
    response = client.get("/qr?url=https://example.com")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_post_qr_complex():
    payload = {
        "url": "https://api.example.com",
        "headers": {"Auth": "token"},
        "body": {"action": "login", "extra": "val"}
    }
    response = client.post("/qr", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    # Note: structure enforced in code

def test_post_qr_encrypted_key():
    payload = {
        "url": "https://example.com",
        "encrypt-key": "testkey"
    }
    response = client.post("/qr/encrypted", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_post_qr_encrypted_token():
    headers = {"X-Encrypt-Token": "token123"}
    payload = {
        "url": "https://example.com",
        "encrypt-token": True
    }
    response = client.post("/qr/encrypted", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_post_qr_invalid_url():
    payload = {"url": "invalid"}
    response = client.post("/qr", json=payload)
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]

def test_post_encrypted_no_token_header():
    payload = {
        "url": "https://example.com",
        "encrypt-token": True
    }
    response = client.post("/qr/encrypted", json=payload)
    assert response.status_code == 400
    assert "no 'X-Encrypt-Token'" in response.json()["detail"]

def test_post_encrypted_mutual_exclusive():
    payload = {
        "url": "https://example.com",
        "encrypt-key": "key",
        "encrypt-token": True
    }
    response = client.post("/qr/encrypted", json=payload)
    assert response.status_code == 400
    assert "only one" in response.json()["detail"].lower()


def test_decrypt_endpoint():
    # Create sample encrypted QR bytes
    from qr_cli.utils import generate_qr_image, encrypt_data
    data = '{"url": "https://example.com", "body": "test"}'
    encrypted = encrypt_data(data, "testkey")
    img_bytes = generate_qr_image(encrypted)
    # Upload with header
    response = client.post(
        "/qr/decrypt",
        files={"file": ("test.png", img_bytes, "image/png")},
        headers={"X-Encrypt-Token": "testkey"}
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["decrypted"]["url"] == "https://example.com"
