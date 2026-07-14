#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-data/input/video.mp4}"
mkdir -p "$(dirname "$OUT")"

ffmpeg -y \
  -f lavfi \
  -i testsrc=size=640x360:rate=30 \
  -f lavfi \
  -i sine=frequency=1000:sample_rate=44100 \
  -t 8 \
  -c:v libx264 \
  -preset ultrafast \
  -pix_fmt yuv420p \
  -c:a aac \
  "$OUT"

echo "sample_video=$OUT"
