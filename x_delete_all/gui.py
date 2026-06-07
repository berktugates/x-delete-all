"""Simple Tkinter GUI for non-technical users"""
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from .storage import TokenStore
from .auth import AuthManager
from .xapi import XAPI
from .db import ArchiveDB
import threading
import json

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('x-delete-all — GUI')
        self.geometry('700x500')
        self.store = TokenStore()
        self.db = ArchiveDB()
        self.token = None
        self.create_widgets()

    def create_widgets(self):
        frm = tk.Frame(self)
        frm.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(frm, text='Step 1 — Authenticate').pack(anchor='w')
        auth_frame = tk.Frame(self)
        auth_frame.pack(fill=tk.X, padx=10)
        tk.Button(auth_frame, text='Authenticate (browser)', command=self.on_auth).pack(side=tk.LEFT)
        tk.Button(auth_frame, text='Paste token manually', command=self.on_paste_token).pack(side=tk.LEFT, padx=6)
        tk.Button(auth_frame, text='Load token', command=self.on_load_token).pack(side=tk.LEFT, padx=6)
        tk.Button(auth_frame, text='What do I need?', command=self.on_explain).pack(side=tk.LEFT, padx=6)

        tk.Label(self, text='Step 2 — Preview & Export').pack(anchor='w', padx=10, pady=(10,0))
        preview_frame = tk.Frame(self)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.preview = scrolledtext.ScrolledText(preview_frame)
        self.preview.pack(fill=tk.BOTH, expand=True)
        pbtns = tk.Frame(self)
        pbtns.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(pbtns, text='Dry-run (fetch)', command=self.on_dry_run).pack(side=tk.LEFT)
        tk.Button(pbtns, text='Export JSON', command=self.on_export).pack(side=tk.LEFT, padx=6)
        tk.Button(pbtns, text='Fetch & Select All', command=self.on_dry_run).pack(side=tk.LEFT, padx=6)

        tk.Label(self, text='Step 3 — Delete (irreversible)').pack(anchor='w', padx=10, pady=(10,0))
        dbtns = tk.Frame(self)
        dbtns.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(dbtns, text='Delete all fetched tweets', command=self.on_delete).pack(side=tk.LEFT)
        tk.Button(dbtns, text='Wipe account (fetch+delete)', command=self.on_wipe).pack(side=tk.LEFT, padx=6)
        tk.Button(dbtns, text='Resume delete', command=self.on_resume).pack(side=tk.LEFT, padx=6)

        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=10, pady=(6,10))
        tk.Label(status_frame, text='Status:').pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value='Idle')
        tk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)

    def set_token_and_save(self, token_dict):
        # token_dict can be raw string or dict
        self.token = token_dict

    def on_auth(self):
        client_id = tk.simpledialog.askstring('Client ID', 'Enter your X app Client ID (create an app in developer portal):')
        if not client_id:
            return
        port = 8080
        auth = AuthManager(client_id=client_id, redirect_port=port)
        def run_auth():
            self.set_status('Opening browser for authentication...')
            token = auth.authenticate()
            if not token:
                self.set_status('Auth failed')
                messagebox.showerror('Auth failed', 'Authentication failed or timed out')
                return
            pwd = tk.simpledialog.askstring('Local password', 'Choose a local password to encrypt the token:')
            if not pwd:
                self.set_status('Auth aborted (no password)')
                messagebox.showwarning('Aborted', 'No password chosen; auth not saved')
                return
            self.store.save_token(token, pwd)
            self.token = token
            self.set_status('Authenticated')
            messagebox.showinfo('Success', 'Authenticated and token saved locally')
        threading.Thread(target=run_auth, daemon=True).start()

    def on_paste_token(self):
        token = tk.simpledialog.askstring('Paste token', 'Paste your OAuth2 token here:')
        if not token:
            return
        pwd = tk.simpledialog.askstring('Local password', 'Choose a local password to encrypt the token:')
        if not pwd:
            return
        # accept both raw token string or full token dict as JSON
        try:
            val = json.loads(token)
        except Exception:
            val = token.strip()
        self.store.save_token(val, pwd)
        messagebox.showinfo('Saved', 'Token saved locally (encrypted)')
        self.set_status('Token saved')

    def on_load_token(self):
        pwd = tk.simpledialog.askstring('Password', 'Enter your local password to unlock token:')
        if not pwd:
            return
        token = self.store.load_token(pwd)
        if not token:
            messagebox.showerror('Error', 'Failed to load token — wrong password or not initialized')
            self.set_status('Failed to load token')
            return
        self.token = token
        messagebox.showinfo('Loaded', 'Token loaded in memory')
        self.set_status('Token loaded')

    def on_explain(self):
        msg = (
            'Two ways to authenticate:\n\n'
            '1) Browser-assisted OAuth (recommended): You need a Client ID from X developer portal.\n'
            '   - Why: the app opens a browser so you can securely log in; no password is shared with us.\n'
            '   - What it provides: a short-lived access token and optional refresh token.\n\n'
            '2) Paste a token manually (advanced): If you already have an OAuth2 token, paste it.\n'
            '   - Why: useful if you use a token manager or already created an app.\n\n'
            'All tokens are encrypted locally with a password and stored under ~/.x-delete-all.\n'
            'The app requests only the scopes needed to read and delete your tweets (tweet.read, tweet.write, users.read, offline.access).'
        )
        messagebox.showinfo('Authentication help', msg)

    def on_dry_run(self):
        # fetch tweets and show preview
        if not self.token:
            messagebox.showwarning('No token', 'Load or authenticate first (or use Demo)')
            return
        api = XAPI(self.token)
        def fetch():
            try:
                self.set_status('Fetching tweets...')
                uid = api.get_user_id()
                tweets = list(api.list_tweets(uid, max_results=5000))
                self.db.store_fetched(tweets)
                self.preview.delete('1.0', tk.END)
                self.preview.insert(tk.END, f"Found {len(tweets)} tweets. Sample:\n\n")
                for t in tweets[:200]:
                    self.preview.insert(tk.END, f"[{t['id']}] {t.get('text','')[:240]}\n\n")
                self.set_status(f'Fetched {len(tweets)} tweets')
            except Exception as e:
                self.set_status('Error fetching')
                messagebox.showerror('Error', str(e))
        threading.Thread(target=fetch, daemon=True).start()

    def on_export(self):
        items = self.db.get_fetched()
        if not items:
            messagebox.showwarning('No data', 'Run dry-run first')
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files','*.json')], initialfile='tweets-export.json')
        if not path:
            return
        with open(path,'w',encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('Exported', f'Exported {len(items)} tweets to {path}')

    def on_delete(self):
        if not messagebox.askyesno('Confirm', 'This will permanently delete ALL fetched tweets from your account. Continue?'):
            return
        pwd = tk.simpledialog.askstring('Password', 'Enter local password to unlock token:')
        if not pwd:
            return
        token = self.store.load_token(pwd)
        if not token:
            messagebox.showerror('Error', 'Failed to load token')
            return
        api = XAPI(token)
        def do_delete():
            tweets = self.db.get_fetched()
            total = len(tweets)
            self.set_status(f'Deleting {total} tweets...')
            deleted = 0
            for t in tweets:
            if self.db.is_deleted(t['id']):
                continue
            ok = api.delete_tweet(t['id'])
            if ok:
                self.db.mark_deleted(t['id'])
                deleted += 1
            self.set_status(f'Delete complete: {deleted}/{total} deleted')
            messagebox.showinfo('Done', f'Delete run complete: {deleted}/{total} deleted')
        threading.Thread(target=do_delete, daemon=True).start()

    def on_resume(self):
        self.on_delete()

    def on_wipe(self):
        # fetch + export + delete flow from GUI with strong confirmation
        if not messagebox.askyesno('Confirm wipe', 'This will fetch ALL tweets, write a local backup, and DELETE them. Continue?'):
            return
        pwd = tk.simpledialog.askstring('Password', 'Enter local password to unlock token:')
        if not pwd:
            return
        token = self.store.load_token(pwd)
        if not token:
            messagebox.showerror('Error', 'Failed to load token')
            return
        api = XAPI(token)
        def run_wipe():
            try:
                self.set_status('Fetching tweets...')
                uid = api.get_user_id()
                tweets = list(api.list_tweets(uid, max_results=100000))
                with open('tweets-export.json','w',encoding='utf-8') as f:
                    json.dump(tweets, f, ensure_ascii=False, indent=2)
                self.db.store_fetched(tweets)
                self.set_status(f'Fetched {len(tweets)} tweets; awaiting final confirmation')
                confirm = tk.simpledialog.askstring('Final confirmation', "Type DELETE to permanently delete all fetched tweets:")
                if confirm != 'DELETE':
                    self.set_status('Wipe aborted')
                    messagebox.showinfo('Aborted', 'Wipe aborted by user')
                    return
                self.set_status('Deleting tweets...')
                failed = 0
                for t in tweets:
                    if self.db.is_deleted(t['id']):
                        continue
                    ok = api.delete_tweet(t['id'])
                    if ok:
                        self.db.mark_deleted(t['id'])
                    else:
                        failed += 1
                self.set_status(f'Wipe complete. Failures: {failed}')
                messagebox.showinfo('Done', f'Wipe complete. Failures: {failed}')
            except Exception as e:
                self.set_status('Error during wipe')
                messagebox.showerror('Error', str(e))
        threading.Thread(target=run_wipe, daemon=True).start()

    def set_status(self, s):
        self.status_var.set(s)

if __name__ == '__main__':
    App().mainloop()
