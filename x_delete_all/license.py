"""Local license verification (signed license files)

Usage:
- Generate a keypair offline (private key kept secret by project maintainers).
- Create license JSON like: {"user":"Name","expires":"2026-12-31","payload":"..."}
- Sign the payload and store base64 signature in license file as field 'sig'.
- Place license file (license.json) next to app and the app will verify it using the embedded public key.
"""
import json
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Replace with the real public key (PEM) used to sign licenses
PUBLIC_KEY_PEM = b"""
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwW...REPLACE_WITH_REAL_KEY...
-----END PUBLIC KEY-----
"""

from cryptography.hazmat.primitives.serialization import load_pem_public_key

def verify_license(path):
    try:
        with open(path,'rb') as f:
            j = json.load(f)
        sig_b64 = j.get('sig')
        if not sig_b64:
            return False, 'No signature found'
        sig = base64.b64decode(sig_b64)
        # prepare payload copy without signature
        payload = dict(j)
        payload.pop('sig', None)
        data = json.dumps(payload, sort_keys=True).encode('utf-8')
        pub = load_pem_public_key(PUBLIC_KEY_PEM)
        pub.verify(sig, data, padding.PKCS1v15(), hashes.SHA256())
        return True, 'OK'
    except Exception as e:
        return False, str(e)
