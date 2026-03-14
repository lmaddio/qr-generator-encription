import argparse
import sys
import json
from qr_cli.utils import validate_url, prepare_qr_data, generate_qr_ascii, generate_qr_image, encrypt_data

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to generate QR codes from URLs (curl-like for complex requests) or decrypt PNG images",
        epilog="Example generate: qr-cli https://example.com --save\nDecrypt: qr-cli --path ./qr.png --encrypt-key mysecret"
    )
    parser.add_argument("url", nargs="?", help="The base URL to encode in QR code (optional for --path decrypt)")
    parser.add_argument("--save", "-s", action="store_true", help="Save QR code as PNG image (qr_code.png)")
    parser.add_argument("--header", "-H", action="append", help="Add header (e.g. -H 'Key: Value') - can be used multiple times")
    parser.add_argument("--data", "-d", help="Request body/data to include in QR (like curl -d)")
    # Encryption options (mutually exclusive, like server)
    parser.add_argument("--encrypt-token", action="store_true", help="Use encryption token from headers (e.g. -H 'X-Encrypt-Token: value')")
    parser.add_argument("--encrypt-key", help="Use this key to encrypt QR content")
    # Decrypt mode (standalone)
    parser.add_argument("--path", "-p", help="Path to QR PNG image for decryption mode (standalone, requires --encrypt-key)")
    
    args = parser.parse_args()
    
    # Parse headers if provided (for complex or token)
    headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                key, value = h.split(":", 1)
                headers[key.strip()] = value.strip()
    
    # Decrypt mode: standalone if --path (ignore generate args, require key)
    if args.path:
        print(f"Decrypting QR image from: {args.path}")
        if not args.encrypt_key:
            print("Error: --path requires --encrypt-key for decryption")
            sys.exit(1)
        try:
            from qr_cli.utils import decode_qr_from_image, decrypt_data
            encrypted_data = decode_qr_from_image(args.path)
            decrypted = decrypt_data(encrypted_data, args.encrypt_key)
            print("Decrypted data:")
            try:
                parsed = json.loads(decrypted)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print("Error: Decrypted data is not valid JSON")
                print(decrypted)
        except Exception as e:
            print(f"Decryption error: {e}")
            sys.exit(1)
        return  # end decrypt mode
    
    # Normal generate mode
    # Validate base URL
    if not validate_url(args.url):
        print("Error: Invalid URL provided. Please provide a valid URL (e.g., https://example.com)")
        sys.exit(1)
    
    # Check encryption options (only one allowed)
    if args.encrypt_token and args.encrypt_key:
        print("Error: Only one of --encrypt-token or --encrypt-key is allowed")
        sys.exit(1)
    
    print(f"Generating QR code for: {args.url}")
    if headers or args.data:
        print(f"  Including headers: {headers}")
        if args.data:
            print(f"  Including body: {args.data}")
    if args.encrypt_token:
        print("  Using encrypt-token from headers")
    if args.encrypt_key:
        print(f"  Using encrypt-key: {args.encrypt_key}")
    
    # For --encrypt-token, get token from headers
    encrypt_token_val = None
    if args.encrypt_token:
        encrypt_token_val = headers.get("X-Encrypt-Token") or headers.get("x-encrypt-token")
        if not encrypt_token_val:
            print("Error: --encrypt-token but no 'X-Encrypt-Token' in headers")
            sys.exit(1)
    
    # Sanitize headers copy for QR: exclude encrypt token header so not in output JSON
    headers_for_qr = {k: v for k, v in headers.items() if k.lower() not in ["x-encrypt-token"]}
    
    # Prepare data (simple URL or JSON with extra info; sanitized headers)
    qr_data = prepare_qr_data(args.url, headers_for_qr, args.data)
    
    # Encrypt if requested
    if args.encrypt_token or args.encrypt_key:
        try:
            qr_data = encrypt_data(qr_data, encrypt_key=args.encrypt_key, encrypt_token=encrypt_token_val)
            print("  QR data encrypted successfully")
        except Exception as e:
            print(f"Encryption error: {e}")
            sys.exit(1)
    
    # Print ASCII
    generate_qr_ascii(qr_data)
    
    if args.save:
        # Save styled PNG
        img_bytes = generate_qr_image(qr_data)  # Note: we save bytes but here for file
        with open("qr_code.png", "wb") as f:
            f.write(img_bytes)
        print("\nQR code saved as qr_code.png")
    else:
        print("\nUse --save to also save as PNG image.")

if __name__ == "__main__":
    main()
