#!/usr/bin/env sh
# Setup for macOS / Linux. Usage: ./install.sh
set -e
cd "$(dirname "$0")"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .

if [ "$(uname)" = "Linux" ]; then
    .venv/bin/python -m playwright install --with-deps chromium || CHROMIUM_FAILED=1
else
    .venv/bin/python -m playwright install chromium || CHROMIUM_FAILED=1
fi
if [ -n "$CHROMIUM_FAILED" ]; then
    echo "WARNING: Chromium could not be downloaded. Install Google Chrome or Microsoft Edge;"
    echo "the tool will use it automatically."
fi

echo
echo "Setup complete. Run: ./run.sh <link> [<link> ...]"
