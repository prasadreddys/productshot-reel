#!/bin/bash
# ProductShot Reel Factory — unit suite + demo e2e. No network, no paid APIs.
set -e
cd "$(dirname "$0")"

echo "=== unit tests ==="
python3 -m unittest discover -s tests -v

echo ""
echo "=== demo e2e: build 5 reels from the example ==="
DEMO="$(mktemp -d /tmp/productshot-demo.XXXXXX)"
python3 -m productshot build --image examples/product.png \
  --product examples/product.json --out "$DEMO"
echo ""
echo "=== demo e2e: check the plan ==="
python3 -m productshot check --plan "$DEMO/plan.json" --dir "$DEMO"
echo ""
echo "=== demo e2e: ffprobe each reel ==="
for f in "$DEMO"/*.mp4; do
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height \
    -show_entries format=duration -of csv=p=0 "$f"
done
echo "demo output: $DEMO"
echo "demo done."
