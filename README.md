# ProductShot Reel Factory v1

One product photo → 5 consistent vertical reels (1080×1920, 6 seconds each,
30fps, H.264 MP4, no audio). Same brand colours, same logo placement, same
CTA across all five — a small seller's whole reel set from one photo.

**Free / $0. No network. No paid APIs. Stdlib + PIL + ffmpeg only.**

## Honest limitation — read this first

Motion is **Ken Burns pan/zoom on the still image** (ffmpeg `zoompan`), not
generated video. The product does not move, the camera does. That is the
whole point: it is honest slideshow motion, and it never pretends to be
AI-generated footage. The sample photo is a PIL-drawn mock, not a real
product photo.

## Quick start

```bash
python3 -m unittest discover -s tests -v   # unit suite
./run_tests.sh                              # unit suite + demo e2e

# 1. Describe the product:
python3 -m productshot init --dir ./my-product
#    edit ./my-product/product.json, replace product.png with your photo

# 2. Build the 5 reels:
python3 -m productshot build --image ./my-product/product.png \
  --product ./my-product/product.json --out ./reels

# 3. Verify them:
python3 -m productshot check --plan ./reels/plan.json --dir ./reels
```

## product.json

```json
{
  "name": "Glow Face Serum",
  "price": "$19.99",
  "currency": "USD",
  "brand": {"primary": "#22c55e", "secondary": "#0f1f16", "text": "#f5f5f0"},
  "cta": "Shop now",
  "logo_text": "GLOW & CO"
}
```

- `name` — non-empty. `price` — `$NN.NN` (e.g. `$19.99`).
- `brand` — `primary`, `secondary`, `text`, each a `#RRGGBB` hex colour.
- `cta`, `logo_text` — non-empty strings.

## The 5 reel templates

| # | Template | What it is |
|---|---|---|
| 1 | `hero` | Full product, slow zoom in |
| 2 | `detail` | Cropped zoom on the product centre, slow pan |
| 3 | `price` | Product with a price / CTA banner in brand colours |
| 4 | `brand` | Product with `logo_text` header and a brand-colour frame |
| 5 | `cta` | Product with a large CTA and price |

Each reel also gets a still frame PNG (its first frame). `build` writes
`plan.json` (one entry per reel: template, file, still, duration, size,
brand colours used, banner rectangle) and `reel-plan.md`.

## `check` — what it actually verifies

- All 5 files exist; each MP4 is 1080×1920 and ~6s (ffprobe).
- Each still is 1080×1920.
- Banner reels: a real PIL pixel check — sampled pixels inside the recorded
  banner rectangle must mostly match the brand primary colour.
- Exit 0 only if everything passes.

## Limitations (honest)

- No audio, no captions, no transitions between reels.
- The product photo is used as-is: bad lighting or a cluttered background
  stays bad lighting. No background removal.
- Text is fitted by shrinking the font; very long product names get small.
- ffmpeg must be installed; if it is missing, `build` fails with a clear
  error instead of writing fake videos.
- `check` verifies the plan's own banner rectangles — it does not re-derive
  where a banner should be.

## Layout

```
productshot/
  productshot/  __init__.py __main__.py cli.py brand.py templates.py render.py
  tests/        stdlib unittest only
  examples/     product.json, product.png (PIL mock), expected-plan.json
  run_tests.sh
```
