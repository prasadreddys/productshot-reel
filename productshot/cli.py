"""CLI for ProductShot Reel Factory."""

import argparse
import json
import os
import sys

from PIL import Image

from .brand import load_product
from .render import (
    banner_pixel_match,
    generate_sample_product_image,
    probe_video,
    render_reel,
    render_still,
)
from .templates import DEFAULT_SECONDS, FPS, HEIGHT, TEMPLATES, WIDTH

SAMPLE_PRODUCT = {
    "name": "Glow Face Serum",
    "price": "$19.99",
    "currency": "USD",
    "brand": {"primary": "#22c55e", "secondary": "#0f1f16", "text": "#f5f5f0"},
    "cta": "Shop now",
    "logo_text": "GLOW & CO",
}


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _write_markdown(path, plan):
    lines = ["# Reel plan — %s" % plan["product_name"], "",
             "Motion is Ken Burns pan/zoom on the still image, not generated video.",
             "", "| Template | File | Duration | Size |",
             "|---|---|---|---|"]
    for reel in plan["reels"]:
        lines.append("| %s | %s | %.1fs | %s |" % (
            reel["template"], reel["file"], reel["duration"], reel["size"]))
    lines += ["", "Brand: primary %s, secondary %s, text %s" % (
        plan["brand"]["primary"], plan["brand"]["secondary"], plan["brand"]["text"])]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def cmd_build(args):
    try:
        product = load_product(args.product)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if not os.path.isfile(args.image):
        print("error: product image not found: %s" % args.image, file=sys.stderr)
        return 2
    seconds = args.seconds
    if seconds <= 0:
        print("error: --seconds must be positive", file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)
    reels = []
    for template in TEMPLATES:
        name = template["name"]
        still, banner_rect = render_still(args.image, product, name)
        still_path = os.path.join(args.out, "%s.png" % name)
        still.save(still_path, "PNG")
        video_path = os.path.join(args.out, "%s.mp4" % name)
        try:
            render_reel(still_path, name, video_path, seconds=seconds, fps=FPS)
        except RuntimeError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        info = probe_video(video_path)
        reels.append({
            "template": name,
            "description": template["description"],
            "file": "%s.mp4" % name,
            "still": "%s.png" % name,
            "duration": round(info["duration"], 2),
            "size": "%dx%d" % (info["width"], info["height"]),
            "brand": {
                "primary": product["brand"]["primary"],
                "secondary": product["brand"]["secondary"],
                "text": product["brand"]["text"],
            },
            "banner_rect": banner_rect,
        })
        print("%s: %s (%.2fs, %s)" % (name, video_path, info["duration"],
                                      reels[-1]["size"]))
    plan = {
        "product_name": product["name"],
        "price": product["price"],
        "brand": {
            "primary": product["brand"]["primary"],
            "secondary": product["brand"]["secondary"],
            "text": product["brand"]["text"],
            "primary_rgb": list(product["brand"]["primary_rgb"]),
        },
        "seconds": seconds,
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "motion": "ken_burns_zoompan",
        "reels": reels,
    }
    _write_json(os.path.join(args.out, "plan.json"), plan)
    _write_markdown(os.path.join(args.out, "reel-plan.md"), plan)
    print("plan: %s" % os.path.join(args.out, "plan.json"))
    return 0


def cmd_check(args):
    try:
        with open(args.plan, "r", encoding="utf-8") as fh:
            plan = json.load(fh)
    except (OSError, ValueError) as exc:
        print("error: cannot read plan %s: %s" % (args.plan, exc), file=sys.stderr)
        return 2
    directory = args.dir
    failures = []
    reels = plan.get("reels", [])
    if len(reels) != 5:
        failures.append("plan must list exactly 5 reels, got %d" % len(reels))
    for reel in reels:
        name = reel.get("template", "?")
        video = os.path.join(directory, reel.get("file", ""))
        still = os.path.join(directory, reel.get("still", ""))
        if not os.path.isfile(video):
            failures.append("%s: missing video %s" % (name, reel.get("file")))
            continue
        try:
            info = probe_video(video)
        except RuntimeError as exc:
            failures.append("%s: ffprobe failed: %s" % (name, exc))
            continue
        if info["width"] != WIDTH or info["height"] != HEIGHT:
            failures.append("%s: video is %dx%d, expected %dx%d" % (
                name, info["width"], info["height"], WIDTH, HEIGHT))
        expected = float(plan.get("seconds", DEFAULT_SECONDS))
        if abs(info["duration"] - expected) > 0.5:
            failures.append("%s: duration %.2fs, expected ~%.1fs" % (
                name, info["duration"], expected))
        if not os.path.isfile(still):
            failures.append("%s: missing still %s" % (name, reel.get("still")))
            continue
        with Image.open(still) as img:
            if img.size != (WIDTH, HEIGHT):
                failures.append("%s: still is %s, expected %dx%d" % (
                    name, img.size, WIDTH, HEIGHT))
        banner_rect = reel.get("banner_rect")
        if banner_rect:
            primary = tuple(plan["brand"]["primary_rgb"])
            match = banner_pixel_match(still, banner_rect, primary)
            print("%s: banner pixels match primary %.0f%%" % (name, match * 100))
            if match < 0.5:
                failures.append("%s: banner pixels match primary only %.0f%%" % (
                    name, match * 100))
        print("%s: OK (%.2fs, %dx%d)" % (name, info["duration"],
                                         info["width"], info["height"]))
    if failures:
        for failure in failures:
            print("FAIL: %s" % failure, file=sys.stderr)
        return 1
    print("check: all %d reels pass" % len(reels))
    return 0


def cmd_init(args):
    os.makedirs(args.dir, exist_ok=True)
    product_path = os.path.join(args.dir, "product.json")
    _write_json(product_path, SAMPLE_PRODUCT)
    image_path = os.path.join(args.dir, "product.png")
    generate_sample_product_image(image_path)
    print("wrote %s" % product_path)
    print("wrote %s" % image_path)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="productshot",
        description="One product photo to 5 consistent vertical reels "
                    "(Ken Burns motion on the still, not generated video).")
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build", help="build 5 reels from a photo + product.json")
    p_build.add_argument("--image", required=True)
    p_build.add_argument("--product", required=True)
    p_build.add_argument("--out", required=True)
    p_build.add_argument("--seconds", type=int, default=DEFAULT_SECONDS)
    p_build.set_defaults(func=cmd_build)
    p_check = sub.add_parser("check", help="verify a plan and its reels")
    p_check.add_argument("--plan", required=True)
    p_check.add_argument("--dir", required=True)
    p_check.set_defaults(func=cmd_check)
    p_init = sub.add_parser("init", help="write a sample product.json + mock photo")
    p_init.add_argument("--dir", required=True)
    p_init.set_defaults(func=cmd_init)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
