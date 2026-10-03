#!/usr/bin/env bash
# Download and unpack a Vosk model into ./models.
set -euo pipefail

MODEL="${1:-vosk-model-small-it-0.22}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/models"

if [[ -d "$DEST/$MODEL" ]]; then
    echo "$MODEL already present in $DEST"
    exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading $MODEL…"
curl -fL --progress-bar -o "$TMP/model.zip" "https://alphacephei.com/vosk/models/$MODEL.zip"
unzip -q "$TMP/model.zip" -d "$DEST"
echo "Installed $DEST/$MODEL"
