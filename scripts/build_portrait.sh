#!/usr/bin/env bash
# Regenerate the ASCII portrait from the GitHub avatar. Deterministic.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/assets/avatar_source.jpg"
OUT="$ROOT/assets/portrait.txt"

curl -sfL --max-time 30 -o "$SRC" "https://avatars.githubusercontent.com/u/1568018?v=4"

TMP="$(mktemp --suffix=.png)"
convert "$SRC" -crop 190x205+90+42 +repage -resize 300% -colorspace Gray \
  -normalize -brightness-contrast 5x18 -unsharp 0x0.8 "$TMP"

jp2a --width=44 --background=light "$TMP" > "$OUT"
rm -f "$TMP"
echo "Wrote $OUT ($(wc -l < "$OUT") lines)"
