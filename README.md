# QR CLI and Backend

## Overview

CLI (`qr-cli`) + FastAPI backend for QR codes from URLs (simple/complex with headers/body). Optional encryption (keys **not** included in QR data). Shared logic in `src/qr_cli/utils.py` (Fernet encryption).

### Installation

```bash
pip install -e .
```

### Tests

Run full tests with coverage (covers all features incl. decryption):
```bash
# CLI tests
python3 -m pytest tests/test_cli.py --cov=qr_cli --cov-report=term-missing -q

# Server tests
python3 -m pytest tests/test_server.py --cov=qr_cli --cov-report=term-missing -q

# All
python3 -m pytest tests/ --cov=qr_cli --cov-report=term-missing -q
```

## CLI Tool (`qr-cli`)

### Usage Examples (all cases)

```bash
# Simple URL
qr-cli https://example.com

# Complex request (headers/body in QR JSON)
qr-cli https://api.example.com -H 'Authorization: Bearer token' -d '{"key":"value"}' --save

# Encrypt with key
qr-cli https://example.com --encrypt-key mysecretkey --save

# Encrypt with token (from header; token excluded from QR)
qr-cli https://example.com -H 'X-Encrypt-Token: token123' --encrypt-token --save

# Help
qr-cli --help
```

**Key behaviors**:
- Validates URL
- ASCII QR in terminal (JSON if complex)
- PNG save only with `--save`/`-s`
- Encryption: `--encrypt-key KEY` **or** `--encrypt-token` (token from `-H 'X-Encrypt-Token: val'`; mutually exclusive; token excluded from output)

## Backend Server

Endpoints:
- **GET /qr?url=...**: Simple PNG
- **POST /qr**: Complex (JSON body) -> PNG
- **POST /qr/encrypted**: Complex + encryption (body flags; headers/body keys + encrypt flags excluded from QR)

### Usage Examples

```bash
# Start
qr-server
# Or: uvicorn qr_cli.server:app --reload

# GET simple
curl -o qr.png "http://localhost:8000/qr?url=https://example.com"

# POST complex
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://api.example.com","headers":{"Auth":"token"},"body":"{\"key\":\"val\"}"}' \
  -o qr.png http://localhost:8000/qr

# POST encrypted (key)
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","encrypt-key":"mysecretkey"}' \
  -o enc_qr.png http://localhost:8000/qr/encrypted

# POST encrypted (token)
curl -X POST -H "Content-Type: application/json" -H "X-Encrypt-Token: token123" \
  -d '{"url":"https://example.com","encrypt-token":true}' \
  -o enc_qr.png http://localhost:8000/qr/encrypted
```

**Key behaviors**:
- Validates URL
- PNG response (no ASCII)
- Encrypt keys/headers excluded from QR JSON
- Runs on http://localhost:8000

## CLI Tool

A command-line tool to generate QR codes from valid URLs (or complex requests), outputting the QR code as ASCII art in the terminal and optionally saving a PNG image.
Supports curl-like flags (`-H`/`--header`, `-d`/`--data`) to embed headers and body into the QR data (as JSON).

### Installation

```bash
pip install -e .
```

### Tests

Run full tests with coverage (covers all features incl. decryption):
```bash
# CLI tests
python3 -m pytest tests/test_cli.py --cov=qr_cli --cov-report=term-missing -q

# Server tests
python3 -m pytest tests/test_server.py --cov=qr_cli --cov-report=term-missing -q

# All
python3 -m pytest tests/ --cov=qr_cli --cov-report=term-missing -q
```

### Usage

```bash
# Simple
qr-cli https://example.com

# Complex (curl-like, encodes headers/body in QR)
qr-cli https://api.example.com -H 'Authorization: Bearer token' -d '{"key": "value"}' --save

# With encryption
qr-cli https://example.com --encrypt-key mysecretkey
```

- Validates base URL
- Prints QR code in terminal (ASCII; encodes full data if headers/body provided)
- Saves `qr_code.png` only with `--save`/`-s`
- Supports `--encrypt-key KEY` or `--encrypt-token TOKEN` (mutually exclusive) to encrypt QR data before generation

## Backend Server

A FastAPI backend server supporting:
- GET `/qr?url=...`: Simple URL QR.
- POST `/qr`: Complex request (JSON body with `url`, optional `headers` dict, optional `body` string). Embeds all info in QR data (as JSON) and returns PNG.
- POST `/qr/encrypted`: Same as above but with encryption (see below).

### Usage

```bash
# Start server
qr-server

# Or with uvicorn directly:
uvicorn qr_cli.server:app --reload

# Test endpoint (returns PNG image):
curl -o qr.png "http://localhost:8000/qr?url=https://example.com"
# Or open in browser: http://localhost:8000/qr?url=https://example.com
```

- Validates URL
- Returns PNG image directly (no ASCII, as it's web)
- Runs on http://localhost:8000 by default