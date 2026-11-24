"""PIL still rendering and ffmpeg Ken Burns motion rendering."""

import json
import os
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

from .templates import FPS, HEIGHT, WIDTH, get_template, zoom_expression

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _font(path, size):
    return ImageFont.truetype(path, size)


def _fit_font(text, max_width, start_size, path=FONT_BOLD, min_size=24):
    """Largest font size (<= start_size) at which text fits max_width."""
    size = start_size
    while size > min_size:
        font = _font(path, size)
        if font.getlength(text) <= max_width:
            return font
        size -= 4
    return _font(path, min_size)


def _text_centered(draw, y, text, font, fill, canvas_width=WIDTH):
    draw.text((canvas_width / 2, y), text, font=font, fill=fill, anchor="ma")


def _load_product_image(path):
    if not os.path.isfile(path):
        raise ValueError("product image not found: %s" % path)
    try:
        img = Image.open(path)
    except Exception as exc:
        raise ValueError("cannot open product image %s: %s" % (path, exc)) from exc
    return img.convert("RGB")


def render_still(image_path, product, template_name):
    """Render the 1080x1920 still for one template.

    Returns (image, banner_rect) where banner_rect is [x0, y0, x1, y1] of
    the solid brand-colour banner when the template has one, else None.
    """
    template = get_template(template_name)
    brand = product["brand"]
    primary = brand["primary_rgb"]
    secondary = brand["secondary_rgb"]
    text_rgb = brand["text_rgb"]

    canvas = Image.new("RGB", (WIDTH, HEIGHT), secondary)
    draw = ImageDraw.Draw(canvas)

    # --- product photo, fitted into the main area -------------------------
    photo = _load_product_image(image_path)
    area_w, area_h = WIDTH - 80, 1180
    photo.thumbnail((area_w, area_h), Image.LANCZOS)
    px = (WIDTH - photo.width) // 2
    py = 200 if template["overlay"] == "brand" else 140
    canvas.paste(photo, (px, py))

    if template["crop"] == "centre":
        # Distinct crop: keep the middle 55% of the canvas, scale back up.
        cx0, cy0 = int(WIDTH * 0.225), int(HEIGHT * 0.22)
        cx1, cy1 = int(WIDTH * 0.775), int(HEIGHT * 0.78)
        canvas = canvas.crop((cx0, cy0, cx1, cy1)).resize((WIDTH, HEIGHT), Image.LANCZOS)
        draw = ImageDraw.Draw(canvas)

    banner_rect = None

    if template["overlay"] == "name":
        font = _fit_font(product["name"], WIDTH - 120, 72)
        _text_centered(draw, HEIGHT - 260, product["name"], font, text_rgb)
        sub = _font(FONT_REG, 40)
        _text_centered(draw, HEIGHT - 170, product["price"], sub, text_rgb)
    elif template["overlay"] == "price":
        banner_rect = [0, HEIGHT - 420, WIDTH, HEIGHT - 180]
        draw.rectangle(banner_rect, fill=primary)
        price_font = _fit_font(product["price"], WIDTH - 160, 110)
        _text_centered(draw, HEIGHT - 400, product["price"], price_font, (255, 255, 255))
        cta_font = _fit_font(product["cta"], WIDTH - 160, 56)
        _text_centered(draw, HEIGHT - 270, product["cta"], cta_font, (255, 255, 255))
        name_font = _fit_font(product["name"], WIDTH - 120, 60)
        _text_centered(draw, HEIGHT - 160, product["name"], name_font, text_rgb)
    elif template["overlay"] == "brand":
        header = [0, 0, WIDTH, 150]
        draw.rectangle(header, fill=primary)
        logo_font = _fit_font(product["logo_text"], WIDTH - 120, 64)
        _text_centered(draw, 38, product["logo_text"], logo_font, (255, 255, 255))
        # Brand-colour frame around the whole canvas.
        for w in range(0, 24, 6):
            draw.rectangle([w, w, WIDTH - 1 - w, HEIGHT - 1 - w], outline=primary, width=6)
        banner_rect = header
        name_font = _fit_font(product["name"], WIDTH - 120, 64)
        _text_centered(draw, HEIGHT - 220, product["name"], name_font, text_rgb)
    elif template["overlay"] == "cta":
        banner_rect = [0, HEIGHT - 520, WIDTH, HEIGHT - 120]
        draw.rectangle(banner_rect, fill=primary)
        cta_font = _fit_font(product["cta"].upper(), WIDTH - 120, 120)
        _text_centered(draw, HEIGHT - 500, product["cta"].upper(), cta_font, (255, 255, 255))
        price_font = _fit_font(product["price"], WIDTH - 160, 84)
        _text_centered(draw, HEIGHT - 330, product["price"], price_font, (255, 255, 255))
        name_font = _fit_font(product["name"], WIDTH - 120, 56)
        _text_centered(draw, HEIGHT - 220, product["name"], name_font, text_rgb)

    return canvas, banner_rect


def render_reel(still_path, template_name, out_path, seconds=6, fps=FPS):
    """Render one MP4 from a still via ffmpeg zoompan (Ken Burns motion).

    Raises RuntimeError if ffmpeg is missing or the render fails.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is not installed — cannot render video")
    frames = int(seconds * fps)
    zoom, x_expr, y_expr = zoom_expression(template_name, frames)
    vf = (
        "zoompan=z='%s':x='%s':y='%s':d=%d:s=%dx%d:fps=%d,"
        "format=yuv420p"
        % (zoom, x_expr, y_expr, frames, WIDTH, HEIGHT, fps)
    )
    cmd = [
        ffmpeg, "-y", "-v", "error",
        "-loop", "1", "-t", str(seconds), "-i", still_path,
        "-vf", vf,
        "-frames:v", str(frames),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("ffmpeg failed for %s: %s" % (template_name, result.stderr.strip()))
    return out_path


def probe_video(path):
    """ffprobe a video. Returns {width, height, duration, codec}."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is not installed — cannot check video")
    cmd = [
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name",
        "-show_entries", "format=duration",
        "-of", "json", path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("ffprobe failed for %s: %s" % (path, result.stderr.strip()))
    data = json.loads(result.stdout)
    if not data.get("streams") or "duration" not in data.get("format", {}):
        raise RuntimeError("ffprobe found no video stream in %s" % path)
    stream = data["streams"][0]
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "duration": float(data["format"]["duration"]),
        "codec": stream["codec_name"],
    }


def banner_pixel_match(still_path, banner_rect, primary_rgb, tolerance=40):
    """Real pixel check: fraction of sampled banner pixels close to primary.

    Samples a grid inside banner_rect (shrunk 10% from its edges) and
    counts pixels whose RGB is within ``tolerance`` of primary_rgb.
    """
    img = Image.open(still_path).convert("RGB")
    x0, y0, x1, y1 = banner_rect
    ix0, iy0 = int(x0 + (x1 - x0) * 0.1), int(y0 + (y1 - y0) * 0.1)
    ix1, iy1 = int(x1 - (x1 - x0) * 0.1), int(y1 - (y1 - y0) * 0.1)
    total, matched = 0, 0
    for sx in range(ix0, ix1, 24):
        for sy in range(iy0, iy1, 24):
            r, g, b = img.getpixel((sx, sy))
            if (abs(r - primary_rgb[0]) <= tolerance
                    and abs(g - primary_rgb[1]) <= tolerance
                    and abs(b - primary_rgb[2]) <= tolerance):
                matched += 1
            total += 1
    return (matched / total) if total else 0.0


def generate_sample_product_image(path):
    """Draw a simple product mock with PIL (not a real photo).

    A coloured background, a product-shaped bottle/jar, and a label.
    Returns the path written.
    """
    img = Image.new("RGB", (900, 1100), (245, 240, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 900, 1100], fill=(245, 240, 230))
    # Shelf line
    draw.rectangle([60, 980, 840, 1000], fill=(210, 200, 185))
    # Bottle body
    draw.rounded_rectangle([330, 380, 570, 980], radius=60, fill=(34, 197, 94))
    # Bottle neck + cap
    draw.rectangle([400, 280, 500, 390], fill=(34, 197, 94))
    draw.rounded_rectangle([390, 230, 510, 285], radius=12, fill=(20, 60, 35))
    # Label
    draw.rounded_rectangle([350, 560, 550, 820], radius=16, fill=(255, 255, 255))
    label_font = _font(FONT_BOLD, 52)
    draw.text((450, 620), "GLOW", font=label_font, fill=(20, 60, 35), anchor="ma")
    sub_font = _font(FONT_REG, 34)
    draw.text((450, 700), "Face Serum", font=sub_font, fill=(60, 60, 60), anchor="ma")
    draw.text((450, 760), "30 ml", font=sub_font, fill=(60, 60, 60), anchor="ma")
    img.save(path, "PNG")
    return path
