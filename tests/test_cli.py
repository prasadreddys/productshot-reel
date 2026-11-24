import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*args):
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT
    return subprocess.run(
        [sys.executable, "-m", "productshot"] + list(args),
        capture_output=True, text=True, env=env, cwd=ROOT,
    )


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _init_example(self):
        result = run_cli("init", "--dir", os.path.join(self.dir, "prod"))
        self.assertEqual(result.returncode, 0, result.stderr)
        return os.path.join(self.dir, "prod")

    def test_init_writes_product_and_photo(self):
        prod = self._init_example()
        self.assertTrue(os.path.isfile(os.path.join(prod, "product.json")))
        self.assertTrue(os.path.isfile(os.path.join(prod, "product.png")))
        with open(os.path.join(prod, "product.json")) as fh:
            data = json.load(fh)
        self.assertEqual(data["name"], "Glow Face Serum")
        self.assertEqual(data["price"], "$19.99")

    def test_build_produces_five_reels_and_plan(self):
        prod = self._init_example()
        out = os.path.join(self.dir, "reels")
        result = run_cli("build", "--image", os.path.join(prod, "product.png"),
                         "--product", os.path.join(prod, "product.json"),
                         "--out", out, "--seconds", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("hero", "detail", "price", "brand", "cta"):
            self.assertTrue(os.path.isfile(os.path.join(out, name + ".mp4")))
            self.assertTrue(os.path.isfile(os.path.join(out, name + ".png")))
        self.assertTrue(os.path.isfile(os.path.join(out, "plan.json")))
        self.assertTrue(os.path.isfile(os.path.join(out, "reel-plan.md")))

    def test_plan_matches_expected_structure(self):
        prod = self._init_example()
        out = os.path.join(self.dir, "reels")
        run_cli("build", "--image", os.path.join(prod, "product.png"),
                "--product", os.path.join(prod, "product.json"),
                "--out", out, "--seconds", "1")
        with open(os.path.join(out, "plan.json")) as fh:
            plan = json.load(fh)
        with open(os.path.join(ROOT, "examples", "expected-plan.json")) as fh:
            expected = json.load(fh)
        self.assertEqual([r["template"] for r in plan["reels"]],
                         [t["name"] for t in expected["templates"]])
        self.assertEqual(plan["width"], expected["width"])
        self.assertEqual(plan["height"], expected["height"])
        self.assertEqual(plan["fps"], expected["fps"])
        self.assertEqual(plan["motion"], expected["motion"])
        self.assertEqual(plan["brand"]["primary"], "#22c55e")

    def test_check_passes_on_good_build(self):
        prod = self._init_example()
        out = os.path.join(self.dir, "reels")
        run_cli("build", "--image", os.path.join(prod, "product.png"),
                "--product", os.path.join(prod, "product.json"),
                "--out", out, "--seconds", "1")
        result = run_cli("check", "--plan", os.path.join(out, "plan.json"),
                         "--dir", out)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("all 5 reels pass", result.stdout)

    def test_check_fails_when_video_deleted(self):
        prod = self._init_example()
        out = os.path.join(self.dir, "reels")
        run_cli("build", "--image", os.path.join(prod, "product.png"),
                "--product", os.path.join(prod, "product.json"),
                "--out", out, "--seconds", "1")
        os.remove(os.path.join(out, "hero.mp4"))
        result = run_cli("check", "--plan", os.path.join(out, "plan.json"),
                         "--dir", out)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stderr)

    def test_build_with_bad_product_exits_2(self):
        prod = self._init_example()
        bad = os.path.join(self.dir, "bad.json")
        with open(bad, "w") as fh:
            json.dump({"name": "", "price": "19.99"}, fh)
        result = run_cli("build", "--image", os.path.join(prod, "product.png"),
                         "--product", bad,
                         "--out", os.path.join(self.dir, "out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", result.stderr)

    def test_build_with_missing_image_exits_2(self):
        prod = self._init_example()
        result = run_cli("build", "--image", os.path.join(self.dir, "nope.png"),
                         "--product", os.path.join(prod, "product.json"),
                         "--out", os.path.join(self.dir, "out"))
        self.assertEqual(result.returncode, 2)

    def test_check_with_missing_plan_exits_2(self):
        result = run_cli("check", "--plan", os.path.join(self.dir, "nope.json"),
                         "--dir", self.dir)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
