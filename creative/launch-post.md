# ProductShot Reel Factory launch post — DRAFT, not published

Status: draft for the user's approval. Nothing posted yet. Repo not created, nothing pushed.

Rules for this post: only measured numbers, no user/sales/revenue claims, no invented quotes. Never call the output AI-generated video — it is Ken Burns motion on a still photo.

## X / Threads version

One product photo. Five vertical reels.

ProductShot Reel Factory turns a single photo + your brand kit into 5 consistent 9:16 reels — hero, detail, price, brand, CTA — same colours, same logo placement, same call to action, ready to post.

Free, open source, stdlib-only Python + PIL + ffmpeg, local files only, no sign-up.

## Longer version (README / Product Hunt style)

Small sellers have one product photo and need a week of reels. ProductShot Reel Factory is the factory: give it the photo and a product.json (name, price, brand colours, CTA) and it renders 5 reels, 1080×1920, 6 seconds each, plus a still per reel and a plan file — with a `check` command that verifies every reel with ffprobe and a real pixel check on the brand banners.

- Demo (mock "GLOW Face Serum", $19.99): 5 reels, all 1080×1920, all 6.00s, all checks PASS; banner pixel match 85–89% (the rest is the white banner text)
- Honest about what it is: Ken Burns pan/zoom on your still photo, not generated video. The product never moves; the camera does.

Measured, not estimated: 36 unit tests, all passing. No network, no keys, no paid API.
