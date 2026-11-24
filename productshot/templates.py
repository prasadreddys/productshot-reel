"""The 5 reel templates.

Every template is a distinct crop/motion/overlay combination over the same
brand kit, so the 5 reels look like one campaign. Motion is Ken Burns
pan/zoom (ffmpeg zoompan) on the rendered still — not generated video.
"""

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DEFAULT_SECONDS = 6


def zoom_expression(template_name, frames):
    """Return (zoom_expr, x_expr, y_expr) for ffmpeg zoompan for a template.

    ``frames`` is the total output frame count (seconds * fps); the detail
    pan needs it to sweep across the frame.
    """
    cx = "iw/2-(iw/zoom/2)"
    cy = "ih/2-(ih/zoom/2)"
    if template_name == "hero":
        return ("min(1+0.0017*on,1.3)", cx, cy)
    if template_name == "detail":
        # Fixed deep zoom, slow pan left -> right across the product.
        return ("1.6", "(iw-iw/zoom)*on/%d" % max(frames - 1, 1), cy)
    if template_name == "price":
        return ("min(1+0.0008*on,1.15)", cx, cy)
    if template_name == "brand":
        return ("min(1+0.0011*on,1.18)", cx, cy)
    if template_name == "cta":
        return ("max(1.2-0.0012*on,1.0)", cx, cy)
    raise ValueError("unknown template: %r" % (template_name,))


TEMPLATES = [
    {
        "name": "hero",
        "description": "Full product, slow zoom in",
        "overlay": "name",
        "crop": "full",
    },
    {
        "name": "detail",
        "description": "Cropped zoom on the product centre, slow pan",
        "overlay": "name",
        "crop": "centre",
    },
    {
        "name": "price",
        "description": "Product with a price / CTA banner in brand colours",
        "overlay": "price",
        "crop": "full",
    },
    {
        "name": "brand",
        "description": "Product with logo_text header and a brand-colour frame",
        "overlay": "brand",
        "crop": "full",
    },
    {
        "name": "cta",
        "description": "Product with a large CTA and price",
        "overlay": "cta",
        "crop": "full",
    },
]


def template_names():
    return [t["name"] for t in TEMPLATES]


def get_template(name):
    for template in TEMPLATES:
        if template["name"] == name:
            return template
    raise ValueError("unknown template: %r" % (name,))
