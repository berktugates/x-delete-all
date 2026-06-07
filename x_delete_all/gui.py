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

        tk.Label(self, text='Step 2 — Preview & Export').pack(anchor='w', padx=10, pady=(10,0))
        preview_frame = tk.Frame(self)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.preview = scrolledtext.ScrolledText(preview_frame)
        self.preview.pack(fill=tk.BOTH, expand=True)
        pbtns = tk.Frame(self)
        pbtns.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(pbtns, text='Dry-run (fetch)', command=self.on_dry_run).pack(side=tk.LEFT)
        tk.Button(pbtns, text='Export JSON', command=self.on_export).pack(side=tk.LEFT, padx=6)

        tk.Label(self, text='Step 3 — Delete (irreversible)').pack(anchor='w', padx=10, pady=(10,0))
        dbtns = tk.Frame(self)
        dbtns.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(dbtns, text='Delete all fetched tweets', command=self.on_delete).pack(side=tk.LEFT)
        tk.Button(dbtns, text='Resume delete', command=self.on_resume).pack(side=tk.LEFT, padx=6)

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
            token = auth.authenticate()
            if not token:
                messagebox.showerror('Auth failed', 'Authentication failed or timed out')
                return
            self.store.save_token(token, tk.simpledialog.askstring('Local password', 'Choose a local password to encrypt the token:'))
            self.token = token
            messagebox.showinfo('Success', 'Authenticated and token saved locally')
        threading.Thread(target=run_auth, daemon=True).start()

    def on_paste_token(self):
        token = tk.simpledialog.askstring('Paste token', 'Paste your OAuth2 token here:')
        if not token:
            return
        pwd = tk.simpledialog.askstring('Local password', 'Choose a local password to encrypt the token:')
        if not pwd:
            return
        self.store.save_token(token.strip(), pwd)
        messagebox.showinfo('Saved', 'Token saved locally (encrypted)')

    def on_load_token(self):
        pwd = tk.simpledialog.askstring('Password', 'Enter your local password to unlock token:')
        if not pwd:
            return
        token = self.store.load_token(pwd)
        if not token:
            messagebox.showerror('Error', 'Failed to load token — wrong password or not initialized')
            return
        self.token = token
        messagebox.showinfo('Loaded', 'Token loaded in memory')

    def on_dry_run(self):
        if not self.token:
            messagebox.showwarning('No token', 'Load or authenticate first')
            return
        api = XAPI(self.token)
        def fetch():
            try:
                uid = api.get_user_id()
                tweets = list(api.list_tweets(uid, max_results=1000))
                self.db.store_fetched(tweets)
                self.preview.delete('1.0', tk.END)
                self.preview.insert(tk.END, f"Found {len(tweets)} tweets. Sample:\n\n")
                for t in tweets[:50]:
                    self.preview.insert(tk.END, f"[{t['id']}] {t.get('text','')[:180]}\n\n")
            except Exception as e:
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
            for t in tweets:
                if self.db.is_deleted(t['id']):
                    continue
                ok = api.delete_tweet(t['id'])
                if ok:
                    self.db.mark_deleted(t['id'])
            messagebox.showinfo('Done', 'Delete run complete')
        threading.Thread(target=do_delete, daemon=True).start()

    def on_resume(self):
        self.on_delete()

if __name__ == '__main__':
    App().mainloop()
