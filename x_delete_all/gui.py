"""Simple Tkinter GUI for non-technical users with onboarding, progress and helpers"""
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
from .storage import TokenStore
from .auth import AuthManager
from .xapi import XAPI
from .db import ArchiveDB
import threading
import json
import os
import logging
import subprocess

LOG_DIR = os.path.join(os.path.expanduser('~'), '.x-delete-all', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOGFILE = os.path.join(LOG_DIR, 'gui.log')
logging.basicConfig(filename=LOGFILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('x-delete-all.gui')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('x-delete-all — GUI')
        self.geometry('780x560')
        self.store = TokenStore()
        self.db = ArchiveDB()
        self.token = None
        self.create_widgets()
        self.after(200, self.show_onboarding_if_first_run)

    def create_widgets(self):
        # Use ttk for a more modern, consistent look and improved accessibility
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('Info.TLabel', font=('Segoe UI', 9))
        style.configure('TButton', padding=6)

        top = ttk.Frame(self, padding=(12,10))
        top.pack(fill=tk.X)

        # Step 1 — Authentication
        ttk.Label(top, text='Step 1 — Authenticate', style='Header.TLabel').pack(anchor='w')
        auth_frame = ttk.Frame(top)
        auth_frame.pack(fill=tk.X, pady=(6,4))
        ttk.Button(auth_frame, text='Authenticate (browser)', command=self.on_auth).pack(side=tk.LEFT)
        ttk.Button(auth_frame, text='Paste token manually', command=self.on_paste_token).pack(side=tk.LEFT, padx=8)
        ttk.Button(auth_frame, text='Load token', command=self.on_load_token).pack(side=tk.LEFT, padx=8)
        ttk.Button(auth_frame, text='What do I need?', command=self.on_explain).pack(side=tk.LEFT, padx=8)
        ttk.Label(top, text='Tip: For a quick trial use Demo mode (no account). For real deletions you must provide an X app Client ID, then choose a local password to encrypt the token.', style='Info.TLabel', wraplength=740).pack(anchor='w', pady=(6,0))

        # Step 2 — Preview & Export
        ttk.Label(self, text='Step 2 — Preview & Export', style='Header.TLabel').pack(anchor='w', padx=12, pady=(12,0))
        preview_frame = ttk.Frame(self)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6,0))
        self.preview = scrolledtext.ScrolledText(preview_frame, height=18, wrap=tk.WORD)
        self.preview.pack(fill=tk.BOTH, expand=True)

        pbtns = ttk.Frame(self)
        pbtns.pack(fill=tk.X, padx=12, pady=8)
        ttk.Button(pbtns, text='Dry-run (fetch)', command=self.on_dry_run).pack(side=tk.LEFT)
        ttk.Button(pbtns, text='Export JSON', command=self.on_export).pack(side=tk.LEFT, padx=8)
        ttk.Button(pbtns, text='Fetch & Select All', command=self.on_dry_run).pack(side=tk.LEFT, padx=8)
        ttk.Button(pbtns, text='Open backup folder', command=self.open_backup_folder).pack(side=tk.LEFT, padx=8)

        # Progress bar (determinate) for delete/wipe operations
        self.progress = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, padx=12, pady=(0,8))

        # Step 3 — Delete
        ttk.Label(self, text='Step 3 — Delete (irreversible)', style='Header.TLabel').pack(anchor='w', padx=12, pady=(6,0))
        dbtns = ttk.Frame(self)
        dbtns.pack(fill=tk.X, padx=12, pady=8)
        ttk.Button(dbtns, text='Delete all fetched tweets', command=self.on_delete).pack(side=tk.LEFT)
        ttk.Button(dbtns, text='Wipe account (fetch+delete)', command=self.on_wipe).pack(side=tk.LEFT, padx=8)
        ttk.Button(dbtns, text='Resume delete', command=self.on_resume).pack(side=tk.LEFT, padx=8)

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=12, pady=(6,12))
        ttk.Label(status_frame, text='Status:', width=8).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value='Idle')
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)

        # Footer quick actions
        footer = ttk.Frame(self)
        footer.pack(fill=tk.X, padx=12, pady=(0,12))
        ttk.Button(footer, text='Try demo (no account)', command=self.on_demo_click).pack(side=tk.RIGHT)
        ttk.Button(footer, text='Open README', command=self.open_help).pack(side=tk.RIGHT, padx=8)

    def set_token_and_save(self, token_dict):
        # token_dict can be raw string or dict
        self.token = token_dict

    def show_onboarding_if_first_run(self):
        # simple first-run check: if no fetched or token exists, show onboarding
        fetched = self.db.get_fetched()
        token_file = os.path.join(os.path.expanduser('~'), '.x-delete-all', 'token.json.enc')
        if not fetched and not os.path.exists(token_file):
            self.show_onboarding()

    def show_onboarding(self):
        win = tk.Toplevel(self)
        win.title('Welcome to x-delete-all')
        win.geometry('520x280')
        tk.Label(win, text='Welcome — safely delete your posts', font=('TkDefaultFont', 14, 'bold')).pack(pady=(12,6))
        tk.Label(win, text='Try demo (no account) or connect your X account to delete your tweets.', wraplength=480).pack(pady=(0,12))
        btns = tk.Frame(win)
        btns.pack(pady=8)
        tk.Button(btns, text='Try demo — no account needed', width=20, command=lambda:[win.destroy(), self.on_demo_click()]).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text='Use my account', width=20, command=lambda:[win.destroy(), self.on_auth()]).pack(side=tk.LEFT, padx=8)
        tk.Button(win, text='Read brief guide', command=lambda: self.open_help()).pack(pady=8)

    def open_help(self):
        # open README or bundled help
        readme = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'README.md'))
        try:
            if os.name == 'nt':
                os.startfile(readme)
            elif sys.platform == 'darwin':
                subprocess.run(['open', readme])
            else:
                subprocess.run(['xdg-open', readme])
        except Exception as e:
            messagebox.showinfo('Help', f'Open README at: {readme}')

    def open_backup_folder(self):
        folder = os.path.join(os.path.expanduser('~'), '.x-delete-all', 'backups')
        os.makedirs(folder, exist_ok=True)
        try:
            if os.name == 'nt':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])
        except Exception:
            messagebox.showinfo('Backup folder', f'Backups are at: {folder}')

    def on_demo_click(self):
        demo = [{'id': f'demo-{i}', 'text': f'Demo tweet {i}'} for i in range(1, 51)]
        self.db.store_fetched(demo)
        self.preview.delete('1.0', tk.END)
        self.preview.insert(tk.END, f"Loaded {len(demo)} demo tweets.\n\n")
        for t in demo[:200]:
            self.preview.insert(tk.END, f"[{t['id']}] {t['text']}\n\n")
        self.set_status('Demo data loaded')

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
        # Allow local-only delete for demo data when no token is loaded
        tweets = self.db.get_fetched()
        if not tweets:
            messagebox.showwarning('No data', 'Run Dry-run first to fetch tweets (or use Demo).')
            return

        if not self.token and all(str(t.get('id','')).startswith('demo-') for t in tweets):
            if not messagebox.askyesno('Confirm', 'This will permanently mark ALL demo tweets as deleted in local archive. Continue?'):
                return
            deleted = 0
            for t in tweets:
                if self.db.is_deleted(t['id']):
                    continue
                self.db.mark_deleted(t['id'])
                deleted += 1
            self.set_status(f'Local demo delete complete: {deleted}/{len(tweets)}')
            messagebox.showinfo('Done', f'Local demo delete complete: {deleted}/{len(tweets)}')
            return

        # otherwise require token
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
        # If demo data loaded (no token), allow local-only wipe
        tweets = self.db.get_fetched()
        if tweets and not self.token and all(str(t.get('id','')).startswith('demo-') for t in tweets):
            if not messagebox.askyesno('Confirm local wipe', 'This will mark all demo tweets as deleted in local archive. Continue?'):
                return
            total = len(tweets)
            self.progress['maximum'] = total
            self.progress['value'] = 0
            deleted = 0
            for t in tweets:
                if self.db.is_deleted(t['id']):
                    self.progress['value'] += 1
                    continue
                self.db.mark_deleted(t['id'])
                deleted += 1
                self.progress['value'] += 1
                self.set_status(f'Local demo deleted {deleted}/{total}')
                self.update_idletasks()
            messagebox.showinfo('Done', f'Local demo wipe complete: {deleted}/{total} marked deleted')
            self.set_status('Local demo wipe complete')
            self.progress['value'] = 0
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

                # write backup to backups directory with timestamp
                bdir = os.path.join(os.path.expanduser('~'), '.x-delete-all', 'backups')
                os.makedirs(bdir, exist_ok=True)
                fname = os.path.join(bdir, f'tweets-export-{int(threading.get_ident())}-{len(tweets)}.json')
                with open(fname,'w',encoding='utf-8') as f:
                    json.dump(tweets, f, ensure_ascii=False, indent=2)

                self.db.store_fetched(tweets)
                total = len(tweets)
                self.set_status(f'Fetched {total} tweets; awaiting final confirmation')
                confirm = tk.simpledialog.askstring('Final confirmation', "Type DELETE to permanently delete all fetched tweets:")
                if confirm != 'DELETE':
                    self.set_status('Wipe aborted')
                    messagebox.showinfo('Aborted', 'Wipe aborted by user')
                    return
                self.set_status('Deleting tweets...')
                failed = 0
                self.progress['maximum'] = total
                self.progress['value'] = 0
                deleted = 0
                for t in tweets:
                    if self.db.is_deleted(t['id']):
                        self.progress['value'] += 1
                        continue
                    ok = api.delete_tweet(t['id'])
                    if ok:
                        self.db.mark_deleted(t['id'])
                        deleted += 1
                    else:
                        failed += 1
                    self.progress['value'] += 1
                    self.set_status(f'Deleted {deleted}/{total} (failed {failed})')
                    self.update_idletasks()
                self.set_status(f'Wipe complete. Deleted: {deleted}. Failures: {failed}. Backup: {fname}')
                messagebox.showinfo('Done', f'Wipe complete. Deleted: {deleted}. Failures: {failed}. Backup: {fname}')
                self.progress['value'] = 0
            except Exception as e:
                self.set_status('Error during wipe')
                messagebox.showerror('Error', str(e))
        threading.Thread(target=run_wipe, daemon=True).start()

    def set_status(self, s):
        self.status_var.set(s)

if __name__ == '__main__':
    App().mainloop()
