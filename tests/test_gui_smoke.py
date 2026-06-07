import os
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog

import pytest

# Smoke test: run GUI in demo mode and perform a local demo wipe programmatically.
# Run headless in CI using Xvfb (workflow installs xvfb and runs xvfb-run).

def test_gui_smoke_demo(tmp_path, monkeypatch):
    # Use a temporary HOME so GUI writes go under tmp_path
    monkeypatch.setenv('HOME', str(tmp_path))

    # Auto-confirm dialogs used during demo wipe
    monkeypatch.setattr(messagebox, 'askyesno', lambda *a, **k: True)
    monkeypatch.setattr(messagebox, 'showinfo', lambda *a, **k: None)
    monkeypatch.setattr(messagebox, 'showerror', lambda *a, **k: None)
    monkeypatch.setattr(simpledialog, 'askstring', lambda *a, **k: 'DELETE')

    # Import App here so it picks up the monkeypatched HOME
    from x_delete_all.gui import App

    app = App()
    try:
        # Load demo data and ensure it was loaded
        app.on_demo_click()
        fetched = app.db.get_fetched()
        assert len(fetched) == 50

        # Run local demo wipe (synchronous path)
        app.on_wipe()

        # All demo items should be marked deleted in the local archive
        fetched_after = app.db.get_fetched()
        assert all(app.db.is_deleted(t['id']) for t in fetched_after)
    finally:
        # Close the Tk app cleanly
        try:
            app.destroy()
        except Exception:
            pass
