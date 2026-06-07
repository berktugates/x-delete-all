#!/usr/bin/env bash
set -e

# Builds a single-file executable for the current platform using PyInstaller.
# Note: building for Windows should be done on Windows, for macOS on macOS, etc.

echo "Installing PyInstaller..."
python3 -m pip install --upgrade pyinstaller

echo "Building standalone executable (one-file)..."
# use the package module path as entrypoint
pyinstaller --onefile --name x-delete-all x_delete_all/cli.py

echo "Executable placed in ./dist/x-delete-all (or ./dist/x-delete-all.exe on Windows)"
