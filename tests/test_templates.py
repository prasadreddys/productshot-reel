import unittest

from productshot.templates import (
    TEMPLATES,
    get_template,
    template_names,
    zoom_expression,
)


class TestTemplates(unittest.TestCase):
    def test_five_templates_in_order(self):
        self.assertEqual(
            template_names(), ["hero", "detail", "price", "brand", "cta"])

    def test_descriptions_distinct_and_nonempty(self):
        descs = [t["description"] for t in TEMPLATES]
        self.assertEqual(len(set(descs)), 5)
        for desc in descs:
            self.assertTrue(desc.strip())

    def test_all_overlays_present(self):
        overlays = {t["overlay"] for t in TEMPLATES}
        self.assertEqual(overlays, {"name", "price", "brand", "cta"})

    def test_zoom_expressions_distinct(self):
        exprs = {zoom_expression(name, 180)[0] for name in template_names()}
        self.assertEqual(len(exprs), 5)

    def test_detail_pan_uses_frame_count(self):
        zoom, x, _y = zoom_expression("detail", 180)
        self.assertEqual(zoom, "1.6")
        self.assertIn("179", x)
        _z, x2, _y2 = zoom_expression("detail", 60)
        self.assertIn("59", x2)

    def test_get_template_unknown_raises(self):
        with self.assertRaises(ValueError):
            get_template("nope")

    def test_hero_zooms_in_cta_zooms_out(self):
        self.assertIn("min(1+", zoom_expression("hero", 180)[0])
        self.assertIn("max(1.2-", zoom_expression("cta", 180)[0])


if __name__ == "__main__":
    unittest.main()
