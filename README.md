# 𝕏 Delete All

Overview
--------
x-delete-all is a local-first utility and GUI that enables users to preview, back up, and permanently delete their X posts from their own machine. The product goal is simple: make the destructive operation transparent, recoverable (locally) and trivial for non-technical users while ensuring no sensitive data leaves the user’s device.

Principles
----------
- Fully local: backups, tokens and archives live under ~/.x-delete-all; nothing is sent to external servers.
- Safe by default: mandatory local backup before destructive actions, explicit typed confirmation for wipes, and a demo mode to practice without risk.
- Non-technical UX: guided onboarding, clear CTAs, and progress indicators for long-running operations.
- Auditable: local JSON exports and an SQLite archive for inspection and resume.

Quick start (for non-technical users)
-------------------------------------
1. Install Python 3.10+ and pip.
2. Clone the repo and prepare an environment (recommended):
   - python -m venv .venv
   - source .venv/bin/activate   (macOS / Linux)
   - .\\.venv\\Scripts\\activate (Windows)
3. Install dependencies:
   - pip install -r requirements.txt
4. Start the GUI in demo mode (no account needed):
   - python -m x_delete_all.gui
   - Onboarding > Try demo — loads safe sample tweets you can preview and delete locally.
5. Use Preview / Export to inspect and save a backup. Use Wipe on demo to see the full flow.

Using your real X account (guided)
----------------------------------
Note: real deletions require OAuth credentials from your X developer account (Client ID). The app does not provide keys.

1. Create an app at the X developer portal and copy the Client ID.
2. In the GUI: click "Authenticate (browser)" and paste the Client ID when prompted.
   - After consent, choose a local password to encrypt the token. Password is only used on your device.
3. Run "Dry-run (fetch)" to preview tweets the app will operate on. Review and Export a JSON backup if you want an external copy.
4. When ready, use "Wipe account (fetch+delete)". The app:
   - Saves a timestamped backup under ~/.x-delete-all/backups
   - Asks for a typed final confirmation (type DELETE)
   - Shows a determinate progress bar during deletion
5. After completion, verify backup and the local archive. Deleted tweets are irreversible on X.

Demo mode vs real mode
----------------------
- Demo mode: safe local-only dataset (IDs like demo-1). Deleting in demo only marks items as deleted in the local archive.
- Real mode: requires OAuth token; deletion calls X API DELETE endpoints. The tool includes rate-limit handling (backoff + jitter).

Safety checklist (must read)
----------------------------
- Always run Dry-run and Export before Delete.
- Keep the backup file in a safe place if you may need to restore records.
- Understand that deletes on X cannot be undone by this tool once performed.

Troubleshooting (non-technical)
-------------------------------
- Browser auth did not complete: make sure your browser opened and you finished consent. If the redirect fails, retry and copy the final URL to the app when prompted.
- Token load fails: the local password must match the one used when saving the token.
- If deletions stop due to rate limits, the app will retry automatically; wait until it finishes or check logs at ~/.x-delete-all/logs/gui.log.

Developer notes (staff‑engineer level)
-------------------------------------
- Token encryption: PBKDF2HMAC (SHA-256, high iteration count) derives an AES key; tokens are encrypted with Fernet and saved as token.json.enc with a salt in salt.bin under ~/.x-delete-all.
- Archive DB: SQLite stores fetched tweets and deletion markers. Supports mark_multiple_deleted and resume operations.
- OAuth: PKCE flow implemented with a local callback server on 127.0.0.1. The user must supply Client ID; refresh token support is included where available.
- API adapter: list_tweets(), delete_tweet(), and rate-limit-aware backoff with jitter. Batch deletes use small inter-request delays to reduce bursts.
- GUI: Tkinter + ttk for portability and a consistent appearance across platforms. Onboarding, demo-first CTA, determinate progress and clear feedback are implemented.

Testing and verification
------------------------
1. Install dependencies: ./scripts/install.sh
2. Run unit tests: pytest -q
3. Manual GUI smoke test (recommended):
   - Start GUI in demo mode and run a full wipe to validate end-to-end flow locally.

Packaging & distribution
------------------------
- PyInstaller: scripts/build_pyinstaller.sh (build on the target OS).
- Briefcase / native installers: scripts/build_briefcase.sh — requires per-OS build host.
- Wheels: scripts/build_wheel.sh

Contributing
------------
Contributions are welcome. Please open issues for bugs or feature requests. For code contributions, follow the project’s branch and pull-request workflow.

Support
-------
Run pytest -q to confirm the codebase works locally. Open an issue in this repository for help or to request prebuilt installers.
