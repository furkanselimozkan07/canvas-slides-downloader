#!/usr/bin/env sh
# Usage: ./run.sh <link> [<link> ...] [options]   (see ./run.sh --help)
# Without -o, files are saved to ~/Downloads.
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "Run ./install.sh first." >&2
    exit 1
fi

case " $* " in
    *" -o "*|*" --output-dir "*|*" --output-dir="*) exec .venv/bin/python -m slides_downloader "$@" ;;
    *) exec .venv/bin/python -m slides_downloader -o "$HOME/Downloads" "$@" ;;
esac
