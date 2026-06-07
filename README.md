x-delete-all — Local bulk-delete tool for X (Twitter)

Summary

x-delete-all is a privacy-first, fully local tool that helps you safely preview, archive and (optionally) delete your X/Twitter posts. Designed for non-technical users: a guided GUI, a simple CLI, and a demo mode that requires no account or keys.

Key features

- Demo mode: try the entire flow without network or keys (safe, local-only).
- Dry-run and export: inspect exactly what would be deleted before any irreversible action.
- Encrypted local tokens: stored under ~/.x-delete-all and protected by a password.
- Resume support and local archive: interruptions are handled and safe to retry.
- GUI for beginners and CLI for power users.

Install (one-time)

1. Install Python 3.11+ from https://python.org.
2. Open a terminal and run the installer for your OS:
   macOS / Linux:   ./scripts/install.sh
   Windows:         scripts\install.bat

Try without any keys (recommended first)

1. Create demo data (no account required):
   python -m x_delete_all.cli demo
2. Preview the demo items:
   python -m x_delete_all.cli dry-run
3. Export if you like:
   python -m x_delete_all.cli export
4. Simulate delete (local only):
   python -m x_delete_all.cli delete

Everything above runs entirely on your machine and requires no keys.

Using the real app with your account

To delete actual tweets you must authenticate with X. Two options exist:

A) Browser-assisted OAuth (recommended):
   python -m x_delete_all.cli auth
   - Follow the prompts. A browser window will open; complete the authorization.
   - Choose a local password to protect the token.

B) Manual token (only if you already have one):
   python -m x_delete_all.cli init
   - Paste the OAuth2 token when prompted.

After authentication:

1. Preview what will be deleted (required):
   python -m x_delete_all.cli dry-run
   This saves a local archive used by export and delete.
2. (Optional) Export the full list:
   python -m x_delete_all.cli export
3. Delete (irreversible):
   python -m x_delete_all.cli delete
   You must type DELETE to confirm — the action is immediate.

GUI (absolute beginners)

To run the GUI locally:
- Double-click a distributed standalone binary (recommended for non-technical users), or run:
  python -c "import x_delete_all.gui as g; g.App().mainloop()"

Testing and verification (run locally)

Run the automated tests to verify your environment and that local flows work:

1. Install dependencies (if not done already): ./scripts/install.sh
2. Run tests: pytest -q

All core tests are included (storage, DB and API mocks). The demo flow exercises the complete UI/CLI experience without requiring API access.

Packaging and installers

- Prebuilt single-file executables: scripts/build_pyinstaller.sh (build on target OS).
- Native installers and polished apps: briefcase (scripts/build_briefcase.sh) — requires per-OS build host.
- Wheels: scripts/build_wheel.sh

Security, privacy and safety

- Tokens are encrypted locally using a password-derived key in ~/.x-delete-all.
- No data is uploaded by default. Exports are local JSON files you may share at your discretion.
- Deleting posts is irreversible. Always run dry-run and export before delete.

Support & contact

- Run pytest -q to confirm everything works on your machine.
- Open an issue in this repo for help or to report a bug.

Notes for maintainers

- Demo mode provides a frictionless path for non-technical users to validate the UX without keys.
- The project is intentionally free and local-first; optional license tooling exists but is disabled for free distribution.

Credits

Created by the x-delete-all maintainers. Contributions welcome — see CONTRIBUTING.md (if present).
