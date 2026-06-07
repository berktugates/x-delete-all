"""Simple sqlite archive DB for fetched tweets and deleted markers"""
import os
import sqlite3
import json

HOME = os.path.expanduser('~')
DB_DIR = os.path.join(HOME, '.x-delete-all')

class ArchiveDB:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_file = os.path.join(DB_DIR, 'archive.sqlite')
        # ensure directory exists
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        self.conn = sqlite3.connect(self.db_file)
        self._init()

    def mark_multiple_deleted(self, ids):
        cur = self.conn.cursor()
        cur.executemany("INSERT OR REPLACE INTO deleted (id, deleted_at) VALUES (?,strftime('%s','now'))", ((i,) for i in ids))
        self.conn.commit()

    def pending_count(self):
        cur = self.conn.cursor()
        cur.execute('SELECT COUNT(*) FROM fetched WHERE id NOT IN (SELECT id FROM deleted)')
        r = cur.fetchone()
        return r[0] if r else 0

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
