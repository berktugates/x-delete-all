#!/usr/bin/env bash
set -e

echo "Building source and wheel distributions..."
python3 -m pip install --upgrade build
python3 -m build

echo "Distributions created in ./dist"
