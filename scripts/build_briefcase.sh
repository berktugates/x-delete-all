#!/usr/bin/env bash
set -e

# Install briefcase and build native apps for the current platform.
python3 -m pip install --upgrade briefcase
# Create native app scaffold (requires briefcase config in pyproject)
briefcase create
briefcase build

echo "Briefcase build complete. See the platforms/ directory for native builds."
