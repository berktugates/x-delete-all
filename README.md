x-delete-all

Purpose

A fully-local CLI tool to let a user delete their X (Twitter) posts in bulk from their own machine. The tool stores nothing remotely — all data and tokens remain on the user's device. It supports dry-run, export, resume, and robust rate-limit handling.

Quickstart (for non-technical users)

1. Install Python 3.11+ from https://python.org if not already installed.
2. Open a terminal and run:
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
3. Recommended (easy) authentication: run the built-in browser auth flow:
   python -m x_delete_all.cli auth
   - When prompted, enter your X app Client ID (follow instructions below to create one).
   - A browser window will open; sign in and authorize the app.
   - Choose a local password when prompted — the token is encrypted locally.

   If you already have an OAuth2 token, you can store it manually:
   python -m x_delete_all.cli init
   Paste the token when requested.

4. Preview what will be deleted (dry-run):
   python -m x_delete_all.cli dry-run
   Review the sample list and confirm it matches what you expect.
5. Export a full list (optional):
   python -m x_delete_all.cli export
6. Delete (irreversible):
   python -m x_delete_all.cli delete
   You will be asked to type DELETE to confirm.

Creating a developer app (Client ID)

- Go to the X developer portal / developer.twitter.com and create a new app/project.
- Under OAuth2 settings, add a redirect URI: http://127.0.0.1:8080/callback
- Copy the Client ID value and use it when running `python -m x_delete_all.cli auth`.

Notes

- The tool stores tokens and fetched tweet lists in ~/.x-delete-all; nothing is uploaded.
- Keep your local password safe; losing it means you cannot decrypt stored tokens.

Packaging and easy installers (for non-technical users)

Option A — Prebuilt standalone executables (recommended for non-technical users):
- On each platform (Windows/macOS/Linux) a single executable can be built with PyInstaller.
- To build locally (developer/machine-specific):
  1. Install dependencies: scripts/install.sh (macOS/Linux) or scripts/install.bat (Windows).
  2. Build a standalone binary: scripts/build_pyinstaller.sh (or build_windows_exe.bat on Windows).
  3. Find the single executable in ./dist/ — distribute that file to users. They can double-click it.

Option B — Install via Python wheel (technical users):
- Build wheel: scripts/build_wheel.sh
- Install: python3 -m pip install dist/x_delete_all-0.1.0-py3-none-any.whl
- Or: upload to PyPI and users can pip install x-delete-all

Notes on cross-platform builds
- PyInstaller produces native executables only for the platform it runs on. To produce macOS binaries, run build on macOS; Windows EXE must be built on Windows.
- For polished installers (DMG/PKG for macOS, MSI for Windows, DEB/RPM/AppImage for Linux) use native packaging tools or Briefcase (https://briefcase.beeware.org/) for a more complete native app.

If you want, create release artifacts next (GitHub Releases + prebuilt binaries) and I will add release automation.

Security & privacy

- Tokens encrypted locally with a password-derived key. No data leaves the machine by default.
- The tool warns before irreversible deletes.

Support

Open issues in this repository if you need help.
