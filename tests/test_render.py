import os
import tempfile
import unittest

from PIL import Image

from productshot.brand import validate_product
from productshot.cli import SAMPLE_PRODUCT
from productshot.render import (
    banner_pixel_match,
    generate_sample_product_image,
    probe_video,
    render_reel,
    render_still,
)
from productshot.templates import HEIGHT, WIDTH

PRODUCT = validate_product(dict(SAMPLE_PRODUCT))


class RenderTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.image = os.path.join(self.tmp.name, "product.png")
        generate_sample_product_image(self.image)


class TestSampleImage(RenderTestCase):
    def test_mock_image_size_and_mode(self):
        with Image.open(self.image) as img:
            self.assertEqual(img.size, (900, 1100))
            self.assertEqual(img.mode, "RGB")

    def test_mock_image_has_green_product(self):
        with Image.open(self.image) as img:
            # Centre of the bottle body is green.
            self.assertEqual(img.getpixel((450, 700))[:3], (255, 255, 255))  # label
            self.assertEqual(img.getpixel((360, 450)), (34, 197, 94))


class TestRenderStill(RenderTestCase):
    def test_hero_size(self):
        still, banner = render_still(self.image, PRODUCT, "hero")
        self.assertEqual(still.size, (WIDTH, HEIGHT))
        self.assertIsNone(banner)

    def test_price_banner_pixels_match_primary(self):
        still, banner = render_still(self.image, PRODUCT, "price")
        self.assertIsNotNone(banner)
        path = os.path.join(self.tmp.name, "price.png")
        still.save(path)
        match = banner_pixel_match(path, banner, (34, 197, 94))
        # Banner text (white) covers part of the sampled area, so the
        # match is high but not 100% — 0.8 is the honest bar here.
        self.assertGreaterEqual(match, 0.8)

    def test_brand_header_pixels_match_primary(self):
        still, banner = render_still(self.image, PRODUCT, "brand")
        self.assertIsNotNone(banner)
        path = os.path.join(self.tmp.name, "brand.png")
        still.save(path)
        match = banner_pixel_match(path, banner, (34, 197, 94))
        self.assertGreaterEqual(match, 0.8)

    def test_detail_crop_differs_from_hero(self):
        hero, _ = render_still(self.image, PRODUCT, "hero")
        detail, _ = render_still(self.image, PRODUCT, "detail")
        self.assertNotEqual(list(hero.getdata()), list(detail.getdata()))

    def test_cta_banner_present(self):
        still, banner = render_still(self.image, PRODUCT, "cta")
        self.assertIsNotNone(banner)
        self.assertEqual(still.size, (WIDTH, HEIGHT))

    def test_banner_match_low_for_wrong_colour(self):
        still, banner = render_still(self.image, PRODUCT, "price")
        path = os.path.join(self.tmp.name, "price.png")
        still.save(path)
        match = banner_pixel_match(path, banner, (255, 0, 0))
        self.assertLess(match, 0.1)


class TestRenderReel(RenderTestCase):
    def test_reel_is_1080x1920_and_about_1s(self):
        still, _ = render_still(self.image, PRODUCT, "hero")
        still_path = os.path.join(self.tmp.name, "hero.png")
        still.save(still_path)
        out = os.path.join(self.tmp.name, "hero.mp4")
        render_reel(still_path, "hero", out, seconds=1)
        info = probe_video(out)
        self.assertEqual((info["width"], info["height"]), (WIDTH, HEIGHT))
        self.assertAlmostEqual(info["duration"], 1.0, delta=0.2)
        self.assertEqual(info["codec"], "h264")

    def test_probe_non_video_raises(self):
        with self.assertRaises(RuntimeError):
            probe_video(self.image)

    def tearDown(self):
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
