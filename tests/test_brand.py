import copy
import unittest

from productshot.brand import parse_hex_color, validate_product

GOOD = {
    "name": "Glow Face Serum",
    "price": "$19.99",
    "currency": "USD",
    "brand": {"primary": "#22c55e", "secondary": "#0f1f16", "text": "#f5f5f0"},
    "cta": "Shop now",
    "logo_text": "GLOW & CO",
}


def _bad(**overrides):
    data = copy.deepcopy(GOOD)
    data.update(overrides)
    return data


class TestParseHexColor(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_hex_color("#22c55e"), (34, 197, 94))
        self.assertEqual(parse_hex_color("#000000"), (0, 0, 0))

    def test_rejects_short_hex(self):
        with self.assertRaises(ValueError):
            parse_hex_color("#fff")

    def test_rejects_no_hash(self):
        with self.assertRaises(ValueError):
            parse_hex_color("22c55e")

    def test_rejects_bad_chars(self):
        with self.assertRaises(ValueError):
            parse_hex_color("#zzzzzz")


class TestValidateProduct(unittest.TestCase):
    def test_valid_normalised(self):
        out = validate_product(copy.deepcopy(GOOD))
        self.assertEqual(out["name"], "Glow Face Serum")
        self.assertEqual(out["brand"]["primary_rgb"], (34, 197, 94))
        self.assertEqual(out["brand"]["primary"], "#22c55e")

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            validate_product(_bad(name="   "))

    def test_bad_prices_rejected(self):
        for bad in ("19.99", "$19.9", "$19.999", "$", "", 19.99):
            with self.assertRaises(ValueError, msg=repr(bad)):
                validate_product(_bad(price=bad))

    def test_missing_brand_colour_rejected(self):
        data = copy.deepcopy(GOOD)
        del data["brand"]["text"]
        with self.assertRaises(ValueError):
            validate_product(data)

    def test_empty_cta_rejected(self):
        with self.assertRaises(ValueError):
            validate_product(_bad(cta=""))

    def test_empty_logo_text_rejected(self):
        with self.assertRaises(ValueError):
            validate_product(_bad(logo_text=""))

    def test_non_dict_rejected(self):
        with self.assertRaises(ValueError):
            validate_product(["not", "a", "dict"])


if __name__ == "__main__":
    unittest.main()
