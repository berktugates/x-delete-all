#!/usr/bin/env bash
set -e

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Dependencies installed. Run 'python3 -m x_delete_all.cli auth' to authenticate, or 'python3 -m x_delete_all.cli init' to paste a token."