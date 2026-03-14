import json
import qrcode
import validators
from io import BytesIO
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
import sys
import base64
from cryptography.fernet import Fernet

def validate_url(url: str) -> bool:
    """Validate if the input is a valid URL."""
    return validators.url(url)

def prepare_qr_data(url: str, headers: dict = None, body: dict | str = None) -> str:
    """Prepare data for QR encoding: basic URL or complex.
    For complex: include request headers + all body keys (except url extracted).
    """
    if headers or body:
        # Encode full request info into QR JSON
        data = {"url": url}
        if headers:
            data["headers"] = dict(headers)  # clone
        if body:
            # If body is dict, include all its keys (rest besides url)
            if isinstance(body, dict):
                for k, v in body.items():
                    if k != "url":
                        data[k] = v
            else:
                # string body
                data["body"] = body
        return json.dumps(data, ensure_ascii=False)
    return url

def generate_qr_ascii(data: str):
    """Generate and print QR as ASCII in terminal."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(out=sys.stdout, tty=False)

def generate_qr_image(data: str) -> bytes:
    """Generate QR code as PNG bytes (styled)."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def encrypt_data(data: str, encrypt_key: str = None, encrypt_token: str = None) -> str:
    """Encrypt the QR data string using provided key or token.
    Uses Fernet symmetric encryption (key derived from input).
    Only one of encrypt_key or encrypt_token should be used.
    """
    if not encrypt_key and not encrypt_token:
        return data
    if encrypt_key and encrypt_token:
        raise ValueError("Only one of encrypt-key or encrypt-token allowed")
    
    # Use key or token as base for Fernet key (32 bytes padded)
    key_str = encrypt_key or encrypt_token
    # Derive secure key
    key_bytes = base64.urlsafe_b64encode(key_str.encode('utf-8').ljust(32)[:32])
    fernet = Fernet(key_bytes)
    encrypted = fernet.encrypt(data.encode('utf-8'))
    return encrypted.decode('utf-8')  # return as str for QR


def decrypt_data(encrypted_data: str, key: str) -> str:
    """Decrypt Fernet-encrypted QR data using key."""
    try:
        key_bytes = base64.urlsafe_b64encode(key.encode('utf-8').ljust(32)[:32])
        fernet = Fernet(key_bytes)
        decrypted = fernet.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
        return decrypted
    except Exception:
        raise ValueError("Decryption failed. Invalid key or data.")


def decode_qr_from_image(image_path: str) -> str:
    """Decode QR code from PNG image using pyzbar, return data string."""
    from pyzbar.pyzbar import decode
    from PIL import Image
    img = Image.open(image_path)
    decoded = decode(img)
    if not decoded:
        raise ValueError("No QR code found in image")
    return decoded[0].data.decode('utf-8')
