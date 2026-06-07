#!/usr/bin/env python3
"""License keypair generator and signer (local tool for maintainers).

Usage:
  - Generate keys: python scripts/license_tool.py gen-keys --out-dir keys
  - Sign license: python scripts/license_tool.py sign --keys keys --license license.json --out signed-license.json

Note: private key should be kept secret by maintainers. The public key can be embedded in the app for offline verification.
"""
import argparse
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes


def gen_keys(out_dir: Path, passphrase: bytes | None = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()
    # private
    if passphrase:
        enc_alg = serialization.BestAvailableEncryption(passphrase)
    else:
        enc_alg = serialization.NoEncryption()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc_alg,
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    (out_dir / 'private_key.pem').write_bytes(priv_pem)
    (out_dir / 'public_key.pem').write_bytes(pub_pem)
    print('Wrote keys to', out_dir)


def sign_license(keys_dir: Path, license_file: Path, out_file: Path, passphrase: bytes | None = None):
    priv_pem = (keys_dir / 'private_key.pem').read_bytes()
    if passphrase:
        priv = serialization.load_pem_private_key(priv_pem, password=passphrase)
    else:
        priv = serialization.load_pem_private_key(priv_pem, password=None)
    lic = json.loads(license_file.read_text(encoding='utf-8'))
    payload = dict(lic)
    payload.pop('sig', None)
    data = json.dumps(payload, sort_keys=True).encode('utf-8')
    sig = priv.sign(data, padding.PKCS1v15(), hashes.SHA256())
    import base64
    lic['sig'] = base64.b64encode(sig).decode('ascii')
    out_file.write_text(json.dumps(lic, indent=2), encoding='utf-8')
    print('Wrote signed license to', out_file)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')
    g = sub.add_parser('gen-keys')
    g.add_argument('--out-dir', required=True)
    g.add_argument('--passphrase', help='Optional passphrase to encrypt private key')

    s = sub.add_parser('sign')
    s.add_argument('--keys', required=True)
    s.add_argument('--license', required=True)
    s.add_argument('--out', required=True)
    s.add_argument('--passphrase', help='Passphrase if private key is encrypted')

    args = p.parse_args()
    if args.cmd == 'gen-keys':
        gen_keys(Path(args.out_dir), args.passphrase.encode('utf-8') if args.passphrase else None)
    elif args.cmd == 'sign':
        sign_license(Path(args.keys), Path(args.license), Path(args.out), args.passphrase.encode('utf-8') if args.passphrase else None)
    else:
        p.print_help()

if __name__ == '__main__':
    main()
