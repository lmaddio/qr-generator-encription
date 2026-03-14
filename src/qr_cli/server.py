from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Header
from fastapi.responses import Response, JSONResponse
import uvicorn
import json
from qr_cli.utils import validate_url, prepare_qr_data, generate_qr_image, encrypt_data, decrypt_data, decode_qr_from_image

app = FastAPI(
    title="QR Code Generator API",
    description="Backend server for generating QR codes from valid URLs (or complex requests with headers/body). Returns PNG image.",
)


@app.get("/qr", response_class=Response)
async def generate_qr_get(
    url: str = Query(..., description="The URL to encode in QR code. Must be valid.")
):
    """
    GET: Simple QR generation from URL.
    Validates URL and returns PNG image.
    """
    try:
        if not validate_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL provided. Please provide a valid URL (e.g., https://example.com)")
        
        # Prepare simple data
        qr_data = prepare_qr_data(url)
        qr_image = generate_qr_image(qr_data)
        return Response(content=qr_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/qr", response_class=Response)
async def generate_qr_post(request: Request):
    """
    POST: Clone original request's headers and body.
    Force QR JSON structure: {'url': , 'headers': , 'body': {all other original body keys except url/encrypt}}.
    Returns PNG image.
    """
    try:
        # Get original request headers (clone)
        headers = dict(request.headers)
        
        # Get and parse body as JSON
        body = await request.json()
        
        # Extract url from body
        url = body.get("url")
        if not url or not validate_url(url):
            raise HTTPException(status_code=400, detail="Invalid or missing 'url' in request body. Provide a valid URL.")
        
        # Build body_for_qr: all original body keys except url/encrypt
        body_for_qr = {k: v for k, v in body.items() if k not in ["url", "encrypt-token", "encrypt-key"]}
        
        # Force exact structure for QR JSON: url, headers, body (nested)
        qr_struct = {
            "url": url,
            "headers": headers,
            "body": body_for_qr
        }
        qr_data = json.dumps(qr_struct, ensure_ascii=False)
        
        qr_image = generate_qr_image(qr_data)
        return Response(content=qr_image, media_type="image/png")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@app.post("/qr/encrypted", response_class=Response)
async def generate_qr_encrypted(request: Request):
    """
    New POST endpoint for encrypted QR.
    Body must include 'url' + optionally 'encrypt-token': true or 'encrypt-key'.
    If encrypt-token=true, expect 'X-Encrypt-Token' header.
    Only one encrypt option allowed.
    Clones headers/body as before, then encrypts QR data.
    """
    try:
        # Get original request headers (clone)
        headers = dict(request.headers)
        
        # Get and parse body as JSON
        body = await request.json()
        
        # Extract url from body
        url = body.get("url")
        if not url or not validate_url(url):
            raise HTTPException(status_code=400, detail="Invalid or missing 'url' in request body.")
        
        # Check encrypt options in body (only one)
        encrypt_token_flag = body.get("encrypt-token") is True
        encrypt_key = body.get("encrypt-key")
        if encrypt_token_flag and encrypt_key:
            raise HTTPException(status_code=400, detail="Only one of 'encrypt-token' or 'encrypt-key' allowed in body.")
        
        # If encrypt-token, get from header
        token = None
        if encrypt_token_flag:
            token = headers.get("x-encrypt-token") or headers.get("X-Encrypt-Token")
            if not token:
                raise HTTPException(status_code=400, detail="encrypt-token=true but no 'X-Encrypt-Token' header found.")
        
        # Sanitize: remove encrypt-token header from headers (not in QR JSON)
        headers_for_qr = {k: v for k, v in headers.items() if k.lower() not in ["x-encrypt-token"]}
        
        # Build body_for_qr: all original body keys except url/encrypt
        body_for_qr = {k: v for k, v in body.items() if k not in ["url", "encrypt-token", "encrypt-key"]}
        
        # Force exact structure for QR JSON: url, headers, body (nested) -- then encrypt if needed
        qr_struct = {
            "url": url,
            "headers": headers_for_qr,
            "body": body_for_qr
        }
        qr_data = json.dumps(qr_struct, ensure_ascii=False)
        
        # Encrypt if requested (after structure)
        if encrypt_token_flag or encrypt_key:
            try:
                qr_data = encrypt_data(qr_data, encrypt_key=encrypt_key, encrypt_token=token)
            except Exception as enc_err:
                raise HTTPException(status_code=400, detail=f"Encryption failed: {str(enc_err)}")
        
        qr_image = generate_qr_image(qr_data)
        return Response(content=qr_image, media_type="image/png")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@app.post("/qr/decrypt", response_class=JSONResponse)
async def decrypt_qr(
    file: UploadFile = File(...),
    x_encrypt_token: str = Header(None, alias="X-Encrypt-Token")
):
    """
    POST /qr/decrypt: Upload PNG QR image + X-Encrypt-Token header.
    Decodes QR, decrypts with token, returns JSON content or error.
    """
    try:
        if not x_encrypt_token:
            raise HTTPException(status_code=400, detail="Missing X-Encrypt-Token header")
        
        # Save upload to temp for decode
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            # Decode and decrypt
            encrypted_data = decode_qr_from_image(tmp_path)
            decrypted = decrypt_data(encrypted_data, x_encrypt_token)
            # Try parse JSON
            try:
                parsed = json.loads(decrypted)
                return {"decrypted": parsed, "raw": decrypted}
            except json.JSONDecodeError:
                return {"error": "Decrypted data is not valid JSON", "raw": decrypted}
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
