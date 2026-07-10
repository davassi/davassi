#!/usr/bin/env bash
# Regenerate the ASCII portrait from a source headshot. Deterministic.
# Usage: build_portrait.sh [SOURCE_IMAGE]   (default: assets/portrait_source.jpg)
# The source photo is intentionally NOT committed (see .gitignore); the committed
# artifact is assets/portrait.txt, which today.py injects into both SVGs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOT/assets/portrait_source.jpg}"
OUT="$ROOT/assets/portrait.txt"

TMP="$(mktemp --suffix=.png)"
# Crop on the head+shoulders, grayscale, normalize, whiten the light
# background, edge-emphasis (sharper face), contrast.
# The crop box is tuned for the 1024x1024 headshot; re-tune for a different photo.
convert "$SRC" -crop 860x900+80+40 +repage -colorspace Gray -normalize \
  -level 0%,94% -unsharp 0x3+1.2+0 -sigmoidal-contrast 4x50% "$TMP"

jp2a --width=72 --background=light "$TMP" > "$OUT"
rm -f "$TMP"
echo "Wrote $OUT ($(wc -l < "$OUT") lines) from $SRC"
