#!/usr/bin/env python3
"""Tests for validators.py"""

import unittest
import tempfile
from pathlib import Path

from PIL import Image


class TestValidateGif(unittest.TestCase):

    def _create_gif(self, width, height, frames=1, duration=100):
        """Create a temporary GIF file and return its path."""
        path = Path(tempfile.mktemp(suffix=".gif"))
        imgs = []
        for i in range(frames):
            img = Image.new("RGBA", (width, height), color=(i * 30, 100, 200, 255))
            imgs.append(img)
        imgs[0].save(
            path,
            save_all=True,
            append_images=imgs[1:],
            duration=duration,
            loop=0,
        )
        self._temp_files.append(path)
        return path

    def setUp(self):
        self._temp_files = []

    def tearDown(self):
        for p in self._temp_files:
            p.unlink(missing_ok=True)

    def _validate(self, gif_path, **kwargs):
        # Import here to keep module-level import errors contained
        from validators import validate_gif
        return validate_gif(gif_path, verbose=False, **kwargs)

    # --- File not found ---

    def test_nonexistent_file(self):
        passes, results = self._validate("/tmp/does_not_exist_12345.gif")
        self.assertFalse(passes)
        self.assertIn("error", results)

    # --- Emoji validation ---

    def test_optimal_emoji_128x128(self):
        path = self._create_gif(128, 128)
        passes, results = self._validate(path, is_emoji=True)
        self.assertTrue(passes)
        self.assertTrue(results["optimal"])

    def test_acceptable_emoji_64x64(self):
        path = self._create_gif(64, 64)
        passes, results = self._validate(path, is_emoji=True)
        self.assertTrue(passes)

    def test_acceptable_emoji_96x96(self):
        path = self._create_gif(96, 96)
        passes, results = self._validate(path, is_emoji=True)
        self.assertTrue(passes)

    def test_emoji_non_square_fails(self):
        path = self._create_gif(128, 64)
        passes, results = self._validate(path, is_emoji=True)
        self.assertFalse(passes)

    def test_emoji_too_small_fails(self):
        path = self._create_gif(32, 32)
        passes, results = self._validate(path, is_emoji=True)
        self.assertFalse(passes)

    def test_emoji_too_large_fails(self):
        path = self._create_gif(256, 256)
        passes, results = self._validate(path, is_emoji=True)
        self.assertFalse(passes)

    # --- Message GIF validation ---

    def test_message_gif_valid(self):
        path = self._create_gif(640, 480)
        passes, results = self._validate(path, is_emoji=False)
        self.assertTrue(passes)

    def test_message_gif_valid_square(self):
        path = self._create_gif(320, 320)
        passes, results = self._validate(path, is_emoji=False)
        self.assertTrue(passes)

    def test_message_gif_bad_aspect_ratio(self):
        path = self._create_gif(640, 200)  # ratio > 2.0
        passes, results = self._validate(path, is_emoji=False)
        self.assertFalse(passes)

    def test_message_gif_too_small(self):
        path = self._create_gif(200, 200)
        passes, results = self._validate(path, is_emoji=False)
        self.assertFalse(passes)

    # --- Results dict ---

    def test_results_contain_expected_keys(self):
        path = self._create_gif(128, 128, frames=3, duration=50)
        passes, results = self._validate(path, is_emoji=True)
        for key in ("width", "height", "size_kb", "frame_count", "fps", "is_emoji"):
            with self.subTest(key=key):
                self.assertIn(key, results)
        self.assertEqual(results["width"], 128)
        self.assertEqual(results["height"], 128)
        self.assertEqual(results["frame_count"], 3)

    # --- Multi-frame ---

    def test_multi_frame_gif(self):
        path = self._create_gif(128, 128, frames=5, duration=100)
        passes, results = self._validate(path, is_emoji=True)
        self.assertTrue(passes)
        self.assertEqual(results["frame_count"], 5)
        self.assertAlmostEqual(results["fps"], 10.0, places=1)


if __name__ == "__main__":
    unittest.main()
