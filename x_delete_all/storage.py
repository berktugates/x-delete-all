"""Local encrypted token storage using password-derived key"""
import os
import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

HOME = os.path.expanduser('~')
BASE_DIR = os.path.join(HOME, '.x-delete-all')

class TokenStore:
    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)

    def _token_paths(self):
        token_file = os.path.join(BASE_DIR, 'token.json.enc')
        salt_file = os.path.join(BASE_DIR, 'salt.bin')
        return token_file, salt_file

    def _derive(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def save_token(self, token, password):
        """Save token dict or raw string as encrypted JSON."""
        if isinstance(token, dict):
            token_data = token
        else:
            token_data = {'access_token': str(token)}
        salt = os.urandom(16)
        key = self._derive(password, salt)
        f = Fernet(key)
        token_b = json.dumps(token_data).encode('utf-8')
        enc = f.encrypt(token_b)
        token_file, salt_file = self._token_paths()
        # ensure dir exists
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, 'wb') as fh:
            fh.write(enc)
        with open(salt_file, 'wb') as fh:
            fh.write(salt)

    def load_token(self, password):
        """Return token dict or None on failure."""
        try:
            token_file, salt_file = self._token_paths()
            with open(salt_file, 'rb') as fh:
                salt = fh.read()
            key = self._derive(password, salt)
            f = Fernet(key)
            with open(token_file, 'rb') as fh:
                enc = fh.read()
            dec = f.decrypt(enc)
            return json.loads(dec.decode('utf-8'))
        except Exception:
            return None

    def update_token(self, token_dict, password):
        """Overwrite stored token with new token dict."""
        self.save_token(token_dict, password)
