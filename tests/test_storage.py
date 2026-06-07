import os
import json
import tempfile
import shutil
import pytest

import x_delete_all.storage as storage


def test_save_and_load_token(tmp_path, monkeypatch):
    # point BASE_DIR to tmp
    monkeypatch.setattr(storage, 'BASE_DIR', str(tmp_path))
    ts = storage.TokenStore()
    pwd = 'testpass'
    token = {'access_token': 'abc123'}
    ts.save_token(token, pwd)
    loaded = ts.load_token(pwd)
    assert loaded['access_token'] == 'abc123'

    # wrong password
    assert ts.load_token('wrong') is None
