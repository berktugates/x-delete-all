@echo off
REM Build a standalone Windows EXE with PyInstaller (run on Windows)
python -m pip install --upgrade pyinstaller
pyinstaller --onefile --name x-delete-all x_delete_all\cli.py
echo Built: dist\x-delete-all.exe
