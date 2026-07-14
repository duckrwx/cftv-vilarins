#!/usr/bin/env bash
set -euo pipefail

BASE_PACKAGE="${1:-data/packages/camera-001-20260615T210000Z}"
OUT_DIR="${2:-data/tampered}"

rm -rf "$OUT_DIR"/case-*
mkdir -p "$OUT_DIR"

cp -a "$BASE_PACKAGE" "$OUT_DIR/case-01-segment-bytes-modified"
printf 'tamper' >> "$OUT_DIR/case-01-segment-bytes-modified/data/segments/segment_0001.mp4"

cp -a "$BASE_PACKAGE" "$OUT_DIR/case-02-segment-removed"
rm "$OUT_DIR/case-02-segment-removed/data/segments/segment_0002.mp4"

cp -a "$BASE_PACKAGE" "$OUT_DIR/case-03-manifest-modified"
python3 - <<'PY'
import json
from pathlib import Path

path = Path("data/tampered/case-03-manifest-modified/data/hour_manifest.json")
data = json.loads(path.read_text(encoding="utf-8"))
data["camera_id"] = "camera-999"
path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
PY

cp -a "$BASE_PACKAGE" "$OUT_DIR/case-04-segment-reordered-in-manifest"
python3 - <<'PY'
import json
from pathlib import Path

path = Path("data/tampered/case-04-segment-reordered-in-manifest/data/hour_manifest.json")
data = json.loads(path.read_text(encoding="utf-8"))
segments = data["segments"]
segments[1], segments[2] = segments[2], segments[1]
path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
PY

echo "Casos adulterados criados em $OUT_DIR"
