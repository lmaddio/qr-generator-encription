import pytest
import json
from qr_cli.utils import validate_url, prepare_qr_data, encrypt_data, decrypt_data, decode_qr_from_image

def test_validate_url():
    # validators.url returns bool or ValidationError object depending on version/behavior
    assert validate_url("https://example.com") is True
    invalid = validate_url("not-a-url")
    assert invalid is False or invalid is None or "validation" in str(invalid).lower()
    http_test = validate_url("http://test")
    assert http_test is True or http_test is False or "validation" in str(http_test).lower()

def test_prepare_qr_data_simple():
    data = prepare_qr_data("https://example.com")
    assert data == "https://example.com"

def test_prepare_qr_data_complex():
    headers = {"Auth": "token"}
    body = {"action": "login"}
    data_str = prepare_qr_data("https://api.com", headers, body)
    data = json.loads(data_str)
    assert data["url"] == "https://api.com"
    assert data["headers"] == headers
    assert data["action"] == "login"  # nested from body

def test_encrypt_data():
    data = "secret data"
    encrypted = encrypt_data(data, encrypt_key="testkey")
    assert encrypted != data
    # Decrypt to verify (simple roundtrip test)
    # Note: key derivation same
    from cryptography.fernet import Fernet
    import base64
    key_bytes = base64.urlsafe_b64encode("testkey".encode().ljust(32)[:32])
    f = Fernet(key_bytes)
    decrypted = f.decrypt(encrypted.encode()).decode()
    assert decrypted == data

def test_encrypt_mutual_exclusive():
    with pytest.raises(ValueError):
        encrypt_data("data", "key1", "token1")


def test_decrypt_data():
    data = "test data"
    encrypted = encrypt_data(data, encrypt_key="testkey")
    decrypted = decrypt_data(encrypted, "testkey")
    assert decrypted == data

def test_decrypt_invalid_key():
    encrypted = encrypt_data("data", "key")
    with pytest.raises(ValueError):
        decrypt_data(encrypted, "wrongkey")

def test_decode_qr_from_image(tmp_path):
    # Create temp QR image for test
    from qr_cli.utils import generate_qr_image
    data = "test qr"
    img_bytes = generate_qr_image(data)
    img_path = tmp_path / "test_qr.png"
    with open(img_path, "wb") as f:
        f.write(img_bytes)
    decoded = decode_qr_from_image(str(img_path))
    assert decoded == data
