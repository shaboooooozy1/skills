#!/usr/bin/env python3
"""
Tests for gif_builder.py - GIFBuilder class.
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from gif_builder import GIFBuilder


def _solid_frame(width=48, height=48, color=(255, 0, 0)):
    """Return a solid-color numpy array frame."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :] = color
    return arr


class TestGIFBuilderInit(unittest.TestCase):

    def test_default_dimensions(self):
        builder = GIFBuilder()
        self.assertEqual(builder.width, 480)
        self.assertEqual(builder.height, 480)

    def test_default_fps(self):
        builder = GIFBuilder()
        self.assertEqual(builder.fps, 15)

    def test_custom_dimensions(self):
        builder = GIFBuilder(width=128, height=128, fps=10)
        self.assertEqual(builder.width, 128)
        self.assertEqual(builder.height, 128)
        self.assertEqual(builder.fps, 10)

    def test_frames_initially_empty(self):
        builder = GIFBuilder()
        self.assertEqual(len(builder.frames), 0)


class TestAddFrame(unittest.TestCase):

    def setUp(self):
        self.builder = GIFBuilder(width=48, height=48)

    def test_add_numpy_frame(self):
        self.builder.add_frame(_solid_frame())
        self.assertEqual(len(self.builder.frames), 1)

    def test_add_pil_image(self):
        img = Image.fromarray(_solid_frame())
        self.builder.add_frame(img)
        self.assertEqual(len(self.builder.frames), 1)

    def test_added_frame_is_numpy(self):
        self.builder.add_frame(_solid_frame())
        self.assertIsInstance(self.builder.frames[0], np.ndarray)

    def test_frame_auto_resize(self):
        # Frame with different dimensions should be resized
        big_frame = np.zeros((200, 300, 3), dtype=np.uint8)
        self.builder.add_frame(big_frame)
        self.assertEqual(self.builder.frames[0].shape, (48, 48, 3))

    def test_add_multiple_frames(self):
        for _ in range(5):
            self.builder.add_frame(_solid_frame())
        self.assertEqual(len(self.builder.frames), 5)


class TestAddFrames(unittest.TestCase):

    def test_add_frames_list(self):
        builder = GIFBuilder(width=48, height=48)
        frames = [_solid_frame(color=(i * 10, 0, 0)) for i in range(3)]
        builder.add_frames(frames)
        self.assertEqual(len(builder.frames), 3)


class TestClear(unittest.TestCase):

    def test_clear_removes_all_frames(self):
        builder = GIFBuilder(width=48, height=48)
        for _ in range(4):
            builder.add_frame(_solid_frame())
        builder.clear()
        self.assertEqual(len(builder.frames), 0)

    def test_can_add_frames_after_clear(self):
        builder = GIFBuilder(width=48, height=48)
        builder.add_frame(_solid_frame())
        builder.clear()
        builder.add_frame(_solid_frame())
        self.assertEqual(len(builder.frames), 1)


class TestDeduplicateFrames(unittest.TestCase):

    def test_identical_frames_removed(self):
        builder = GIFBuilder(width=48, height=48)
        frame = _solid_frame(color=(100, 100, 100))
        for _ in range(5):
            builder.add_frame(frame.copy())
        removed = builder.deduplicate_frames()
        self.assertGreater(removed, 0)
        self.assertEqual(len(builder.frames), 1)

    def test_different_frames_kept(self):
        builder = GIFBuilder(width=48, height=48)
        # Add frames with very different colors so they exceed similarity threshold
        for i in range(5):
            builder.add_frame(_solid_frame(color=(i * 50, 0, 0)))
        original_count = len(builder.frames)
        removed = builder.deduplicate_frames()
        self.assertEqual(removed, 0)
        self.assertEqual(len(builder.frames), original_count)

    def test_single_frame_returns_zero(self):
        builder = GIFBuilder(width=48, height=48)
        builder.add_frame(_solid_frame())
        removed = builder.deduplicate_frames()
        self.assertEqual(removed, 0)

    def test_empty_frames_returns_zero(self):
        builder = GIFBuilder(width=48, height=48)
        removed = builder.deduplicate_frames()
        self.assertEqual(removed, 0)


class TestSave(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_save_raises_on_empty_frames(self):
        builder = GIFBuilder(width=48, height=48)
        with self.assertRaises(ValueError):
            builder.save(Path(self.tmpdir) / "empty.gif")

    def test_save_creates_file(self):
        builder = GIFBuilder(width=48, height=48, fps=10)
        for i in range(3):
            builder.add_frame(_solid_frame(color=(i * 80, 0, 0)))
        output = Path(self.tmpdir) / "out.gif"
        builder.save(output)
        self.assertTrue(output.exists())

    def test_save_returns_info_dict(self):
        builder = GIFBuilder(width=48, height=48, fps=10)
        builder.add_frame(_solid_frame())
        builder.add_frame(_solid_frame(color=(0, 255, 0)))
        output = Path(self.tmpdir) / "info.gif"
        info = builder.save(output)
        self.assertIn("path", info)
        self.assertIn("size_kb", info)
        self.assertIn("dimensions", info)
        self.assertIn("frame_count", info)
        self.assertIn("fps", info)

    def test_save_info_dimensions_match(self):
        builder = GIFBuilder(width=48, height=48, fps=10)
        builder.add_frame(_solid_frame())
        output = Path(self.tmpdir) / "dim.gif"
        info = builder.save(output)
        self.assertEqual(info["dimensions"], "48x48")

    def test_save_info_fps_matches(self):
        builder = GIFBuilder(width=48, height=48, fps=12)
        builder.add_frame(_solid_frame())
        output = Path(self.tmpdir) / "fps.gif"
        info = builder.save(output)
        self.assertEqual(info["fps"], 12)

    def test_save_with_remove_duplicates(self):
        builder = GIFBuilder(width=48, height=48, fps=10)
        frame = _solid_frame(color=(50, 50, 50))
        for _ in range(4):
            builder.add_frame(frame.copy())
        output = Path(self.tmpdir) / "dedup.gif"
        builder.save(output, remove_duplicates=True)
        self.assertTrue(output.exists())

    def test_save_optimize_for_emoji_resizes(self):
        builder = GIFBuilder(width=200, height=200, fps=10)
        for i in range(3):
            builder.add_frame(_solid_frame(width=200, height=200, color=(i * 80, 0, 0)))
        output = Path(self.tmpdir) / "emoji.gif"
        info = builder.save(output, optimize_for_emoji=True)
        self.assertEqual(info["dimensions"], "128x128")


if __name__ == "__main__":
    unittest.main()
