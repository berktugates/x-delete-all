"""OAuth2 PKCE helper for local authentication flow"""
import base64
import hashlib
import os
import secrets
import webbrowser
import threading
import http.server
import urllib.parse as urlparse
import requests
import time
import json

from .xapi import XAPI

AUTH_BASE = 'https://twitter.com/i/oauth2/authorize'
TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'

class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        qs = urlparse.parse_qs(parsed.query)
        code = qs.get('code', [None])[0]
        state = qs.get('state', [None])[0]
        # write simple response
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>You may close this window and return to the app.</h1></body></html>")
        # store in server
        self.server._code = code
        self.server._state = state

    def log_message(self, format, *args):
        # silence logging
        return

class AuthManager:
    def __init__(self, client_id, redirect_port=8080, scopes=None):
        self.client_id = client_id
        self.port = redirect_port
        if scopes is None:
            scopes = ['tweet.read','tweet.write','users.read','offline.access']
        self.scopes = scopes

    def _generate_pkce(self):
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b'=').decode('ascii')
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
        return code_verifier, code_challenge

    def _start_local_server(self):
        server = http.server.HTTPServer(('127.0.0.1', self.port), _CallbackHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.daemon = True
        thread.start()
        return server

    def authenticate(self, timeout=300):
        code_verifier, code_challenge = self._generate_pkce()
        state = secrets.token_urlsafe(16)
        redirect_uri = f'http://127.0.0.1:{self.port}/callback'
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        auth_url = AUTH_BASE + '?' + urlparse.urlencode(params, quote_via=urlparse.quote)
        print('\nOpening your browser to authenticate with X.\nIf nothing opens, paste this URL into your browser:\n')
        print(auth_url + '\n')
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

        server = self._start_local_server()
        start = time.time()
        while time.time() - start < timeout:
            if getattr(server, '_code', None):
                code = server._code
                recv_state = server._state
                if recv_state != state:
                    print('State mismatch, aborting.')
                    return None
                # exchange code
                token = XAPI.exchange_code_for_token(code, code_verifier, redirect_uri, self.client_id)
                return token
            time.sleep(0.5)
        print('Timeout waiting for authentication callback.')
        return None
