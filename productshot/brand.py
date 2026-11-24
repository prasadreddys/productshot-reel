"""Brand colours and product.json validation."""

import json
import re

PRICE_RE = re.compile(r"^\$\d+(\.\d{2})?$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def parse_hex_color(value):
    """Parse '#RRGGBB' into an (r, g, b) tuple. Raises ValueError otherwise."""
    if not isinstance(value, str) or not HEX_RE.match(value):
        raise ValueError("colour must be a hex string like '#22c55e', got %r" % (value,))
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


def hex_of(rgb):
    return "#%02x%02x%02x" % rgb


def load_product(path):
    """Load and validate a product.json file. Returns a normalised dict."""
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError("product.json is not valid JSON: %s" % exc) from exc
    return validate_product(data)


def validate_product(data):
    """Validate a parsed product.json dict. Returns a normalised copy.

    Raises ValueError with a clear message for every rejection case.
    """
    if not isinstance(data, dict):
        raise ValueError("product.json must be a JSON object")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    price = data.get("price")
    if not isinstance(price, str) or not PRICE_RE.match(price):
        raise ValueError("price must look like '$19.99', got %r" % (price,))
    brand = data.get("brand")
    if not isinstance(brand, dict):
        raise ValueError("brand must be an object with primary, secondary and text colours")
    colours = {}
    for key in ("primary", "secondary", "text"):
        if key not in brand:
            raise ValueError("brand.%s is missing" % key)
        colours[key] = parse_hex_color(brand[key])
    cta = data.get("cta")
    if not isinstance(cta, str) or not cta.strip():
        raise ValueError("cta must be a non-empty string")
    logo_text = data.get("logo_text")
    if not isinstance(logo_text, str) or not logo_text.strip():
        raise ValueError("logo_text must be a non-empty string")
    currency = data.get("currency", "USD")
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency must be a non-empty string")
    return {
        "name": name.strip(),
        "price": price,
        "currency": currency.strip(),
        "brand": {
            "primary": hex_of(colours["primary"]),
            "secondary": hex_of(colours["secondary"]),
            "text": hex_of(colours["text"]),
            "primary_rgb": colours["primary"],
            "secondary_rgb": colours["secondary"],
            "text_rgb": colours["text"],
        },
        "cta": cta.strip(),
        "logo_text": logo_text.strip(),
    }
