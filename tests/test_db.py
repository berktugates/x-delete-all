import x_delete_all.db as db
import pytest


def test_store_and_mark_deleted(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_DIR', str(tmp_path))
    adb = db.ArchiveDB()
    tweets = [{'id':'1','text':'hello'},{'id':'2','text':'bye'}]
    adb.store_fetched(tweets)
    got = adb.get_fetched()
    assert len(got) == 2
    adb.mark_deleted('1')
    assert adb.is_deleted('1')
    assert not adb.is_deleted('2')
