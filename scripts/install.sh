#!/usr/bin/env bash
# Create a virtual environment in ./.venv and install THOT.
# Usage: scripts/install.sh [extras]   (default extras: gui,live)
set -euo pipefail

EXTRAS="${1:-gui,live}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"

command -v ffmpeg >/dev/null || echo "warning: ffmpeg not found; some formats may not decode." >&2

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -e "$ROOT[$EXTRAS]"

echo
echo "THOT installed. Activate with:  source .venv/bin/activate"
echo "Then run:  thot --help   |   thot gui   |   thot live"
