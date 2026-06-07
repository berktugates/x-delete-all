"""Simple sqlite archive DB for fetched tweets and deleted markers"""
import os
import sqlite3
import json

HOME = os.path.expanduser('~')
DB_DIR = os.path.join(HOME, '.x-delete-all')
DB_FILE = os.path.join(DB_DIR, 'archive.sqlite')

class ArchiveDB:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS fetched (id TEXT PRIMARY KEY, data TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS deleted (id TEXT PRIMARY KEY, deleted_at INTEGER)''')
        self.conn.commit()

    def store_fetched(self, tweets):
        cur = self.conn.cursor()
        for t in tweets:
            cur.execute('INSERT OR REPLACE INTO fetched (id, data) VALUES (?,?)', (t['id'], json.dumps(t)))
        self.conn.commit()

    def get_fetched(self):
        cur = self.conn.cursor()
        cur.execute('SELECT data FROM fetched')
        rows = cur.fetchall()
        return [json.loads(r[0]) for r in rows]

    def mark_deleted(self, tid):
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO deleted (id, deleted_at) VALUES (?,strftime('%s','now'))", (tid,))
        self.conn.commit()

    def is_deleted(self, tid):
        cur = self.conn.cursor()
        cur.execute('SELECT 1 FROM deleted WHERE id=?', (tid,))
        return cur.fetchone() is not None
