import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
import json
# CLI tests via main entry (no edit to src)

def test_cli_simple(capsys, monkeypatch):
    # Mock args for simple
    monkeypatch.setattr(sys, 'argv', ['qr-cli', 'https://example.com'])
    with patch('qr_cli.main.generate_qr_ascii') as mock_ascii, \
         patch('qr_cli.main.generate_qr_image') as mock_image:
        from qr_cli.main import main
        main()  # no SystemExit in practice
        # Check calls
        assert mock_ascii.called

def test_cli_complex(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['qr-cli', 'https://api.com', '-H', 'Auth: token', '-d', '{"k":"v"}', '--save'])
    with patch('qr_cli.main.generate_qr_ascii'), \
         patch('qr_cli.main.generate_qr_image'), \
         patch('builtins.open', MagicMock()):
        from qr_cli.main import main
        main()  # no exit
        captured = capsys.readouterr()
        assert 'Including headers' in captured.out
        assert 'Including body' in captured.out

def test_cli_encrypt_key(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['qr-cli', 'https://example.com', '--encrypt-key', 'testkey'])
    with patch('qr_cli.main.generate_qr_ascii'), patch('qr_cli.main.generate_qr_image'):
        from qr_cli.main import main
        main()
        captured = capsys.readouterr()
        assert 'encrypted successfully' in captured.out

def test_cli_encrypt_token_from_header(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['qr-cli', 'https://example.com', '-H', 'X-Encrypt-Token: token123', '--encrypt-token'])
    with patch('qr_cli.main.generate_qr_ascii'), patch('qr_cli.main.generate_qr_image'):
        from qr_cli.main import main
        main()
        captured = capsys.readouterr()
        assert 'encrypted successfully' in captured.out
        # Token excluded from QR (but print may show header parse)

def test_cli_invalid_url(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['qr-cli', 'invalid'])
    with pytest.raises(SystemExit):
        from qr_cli.main import main
        main()
    captured = capsys.readouterr()
    assert 'Invalid URL' in captured.out


def test_cli_decrypt_mode(tmp_path, capsys, monkeypatch):
    # Create sample encrypted QR for test
    from qr_cli.utils import generate_qr_image, encrypt_data
    data = '{"url": "https://example.com"}'
    encrypted = encrypt_data(data, "testkey")
    img_bytes = generate_qr_image(encrypted)  # QR of encrypted
    img_path = tmp_path / "test_decrypt.png"
    with open(img_path, "wb") as f:
        f.write(img_bytes)
    # Run CLI decrypt
    monkeypatch.setattr(sys, 'argv', ['qr-cli', '--path', str(img_path), '--encrypt-key', 'testkey'])
    from qr_cli.main import main
    main()
    captured = capsys.readouterr()
    assert 'Decrypted data' in captured.out
    assert 'https://example.com' in captured.out
