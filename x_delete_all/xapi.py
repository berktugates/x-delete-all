"""Minimal X API adapter with rate-limit handling and token support"""
import requests
import time
import random

BASE = "https://api.twitter.com/2"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

class XAPI:
    def __init__(self, token):
        # token may be a dict (token json) or a raw string
        if isinstance(token, dict):
            access = token.get('access_token')
        else:
            access = token
        self.token = access if access and access.startswith('Bearer ') else (f"Bearer {access}" if access else None)
        self.session = requests.Session()
        headers = {'User-Agent': 'x-delete-all/0.1'}
        if self.token:
            headers['Authorization'] = self.token
        self.session.headers.update(headers)

    def _handle_rate(self, resp, attempt):
        if resp is None:
            time.sleep(min(60, 2 ** attempt))
            return True
        if resp.status_code == 429:
            reset = resp.headers.get('x-rate-limit-reset')
            if reset:
                try:
                    now = int(time.time())
                    wait = max(1, int(reset) - now + 1)
                except Exception:
                    wait = min(60, 2 ** attempt)
                jitter = random.random()
                time.sleep(wait + jitter)
                return True
            # fallback exponential backoff with jitter
            time.sleep(min(60, 2 ** attempt) + random.random())
            return True
        return False

    def get_user_id(self):
        url = f"{BASE}/users/me"
        for attempt in range(6):
            resp = self.session.get(url)
            if resp.status_code == 200:
                j = resp.json()
                return j['data']['id']
            if not self._handle_rate(resp, attempt):
                break
        raise RuntimeError(f"Unable to fetch user id: {resp.status_code} {resp.text}")

    def list_tweets(self, user_id, max_results=10000):
        url = f"{BASE}/users/{user_id}/tweets"
        params = {'max_results': 100, 'tweet.fields': 'created_at'}
        next_token = None
        total = 0
        while True:
            if next_token:
                params['pagination_token'] = next_token
            for attempt in range(6):
                resp = self.session.get(url, params=params)
                if resp.status_code == 200:
                    j = resp.json()
                    data = j.get('data', [])
                    for t in data:
                        yield t
                        total += 1
                        if total >= max_results:
                            return
                    meta = j.get('meta', {})
                    next_token = meta.get('next_token')
                    if not next_token:
                        return
                    break
                if self._handle_rate(resp, attempt):
                    continue
                raise RuntimeError(f"List tweets failed: {resp.status_code} {resp.text}")

    def delete_tweet(self, tweet_id):
        url = f"{BASE}/tweets/{tweet_id}"
        for attempt in range(6):
            resp = self.session.delete(url)
            if resp.status_code in (200,204):
                # small pause to avoid bursts
                time.sleep(0.5 + random.random())
                return True
            if self._handle_rate(resp, attempt):
                continue
            # on 403/401, abort
            return False
        return False

    @staticmethod
    def exchange_code_for_token(code, code_verifier, redirect_uri, client_id):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
            'client_id': client_id
        }
        resp = requests.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def refresh_token(refresh_token, client_id):
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id
        }
        resp = requests.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()
