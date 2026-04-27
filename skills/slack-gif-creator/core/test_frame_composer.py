#!/usr/bin/env python3
"""
Tests for frame_composer.py - frame creation and drawing utilities.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from frame_composer import (
    create_blank_frame,
    draw_circle,
    draw_text,
    create_gradient_background,
    draw_star,
)
from PIL import Image


class TestCreateBlankFrame(unittest.TestCase):

    def test_default_white_background(self):
        frame = create_blank_frame(100, 80)
        self.assertEqual(frame.size, (100, 80))
        self.assertEqual(frame.mode, "RGB")
        # Top-left pixel should be white
        self.assertEqual(frame.getpixel((0, 0)), (255, 255, 255))

    def test_custom_color(self):
        frame = create_blank_frame(50, 50, color=(0, 128, 255))
        r, g, b = frame.getpixel((25, 25))
        self.assertEqual(r, 0)
        self.assertEqual(g, 128)
        self.assertEqual(b, 255)

    def test_correct_width(self):
        frame = create_blank_frame(200, 100)
        self.assertEqual(frame.width, 200)

    def test_correct_height(self):
        frame = create_blank_frame(200, 100)
        self.assertEqual(frame.height, 100)

    def test_returns_pil_image(self):
        frame = create_blank_frame(10, 10)
        self.assertIsInstance(frame, Image.Image)

    def test_black_background(self):
        frame = create_blank_frame(10, 10, color=(0, 0, 0))
        self.assertEqual(frame.getpixel((5, 5)), (0, 0, 0))


class TestDrawCircle(unittest.TestCase):

    def setUp(self):
        self.frame = create_blank_frame(200, 200)

    def test_returns_frame(self):
        result = draw_circle(self.frame, (100, 100), 30, fill_color=(255, 0, 0))
        self.assertIsInstance(result, Image.Image)

    def test_returns_same_frame(self):
        result = draw_circle(self.frame, (100, 100), 30, fill_color=(255, 0, 0))
        self.assertIs(result, self.frame)

    def test_draws_fill_color(self):
        frame = create_blank_frame(100, 100, color=(255, 255, 255))
        draw_circle(frame, (50, 50), 10, fill_color=(255, 0, 0))
        # Center pixel should be red
        self.assertEqual(frame.getpixel((50, 50)), (255, 0, 0))

    def test_no_fill_no_error(self):
        draw_circle(self.frame, (100, 100), 30, outline_color=(0, 0, 0))

    def test_frame_size_unchanged(self):
        draw_circle(self.frame, (100, 100), 30, fill_color=(0, 0, 0))
        self.assertEqual(self.frame.size, (200, 200))


class TestDrawText(unittest.TestCase):

    def setUp(self):
        self.frame = create_blank_frame(300, 100)

    def test_returns_frame(self):
        result = draw_text(self.frame, "Hello", (10, 10))
        self.assertIsInstance(result, Image.Image)

    def test_returns_same_frame(self):
        result = draw_text(self.frame, "Hello", (10, 10))
        self.assertIs(result, self.frame)

    def test_centered_text_does_not_raise(self):
        draw_text(self.frame, "Centered", (150, 50), centered=True)

    def test_custom_color_does_not_raise(self):
        draw_text(self.frame, "Red", (10, 10), color=(255, 0, 0))

    def test_empty_string_does_not_raise(self):
        draw_text(self.frame, "", (10, 10))

    def test_frame_size_unchanged(self):
        draw_text(self.frame, "Test", (10, 10))
        self.assertEqual(self.frame.size, (300, 100))


class TestCreateGradientBackground(unittest.TestCase):

    def test_returns_pil_image(self):
        frame = create_gradient_background(100, 100, (255, 0, 0), (0, 0, 255))
        self.assertIsInstance(frame, Image.Image)

    def test_correct_size(self):
        frame = create_gradient_background(150, 80, (0, 0, 0), (255, 255, 255))
        self.assertEqual(frame.size, (150, 80))

    def test_correct_mode(self):
        frame = create_gradient_background(50, 50, (0, 0, 0), (255, 255, 255))
        self.assertEqual(frame.mode, "RGB")

    def test_top_color_at_top(self):
        top_color = (255, 0, 0)
        frame = create_gradient_background(100, 100, top_color, (0, 0, 255))
        r, g, b = frame.getpixel((50, 0))
        self.assertEqual(r, top_color[0])
        self.assertEqual(g, top_color[1])
        self.assertEqual(b, top_color[2])

    def test_bottom_color_near_bottom(self):
        bottom_color = (0, 0, 255)
        frame = create_gradient_background(100, 100, (255, 0, 0), bottom_color)
        # At y=99 (last row), ratio ≈ 0.99, so r ≈ 255*0.01 ≈ 2, b ≈ 255*0.99 ≈ 252
        r, g, b = frame.getpixel((50, 99))
        # Blue channel should be dominant
        self.assertGreater(b, r)

    def test_gradient_changes_along_y(self):
        frame = create_gradient_background(100, 100, (255, 0, 0), (0, 0, 255))
        r_top, _, _ = frame.getpixel((50, 0))
        r_bottom, _, _ = frame.getpixel((50, 99))
        self.assertGreater(r_top, r_bottom)


class TestDrawStar(unittest.TestCase):

    def setUp(self):
        self.frame = create_blank_frame(200, 200)

    def test_returns_frame(self):
        result = draw_star(self.frame, (100, 100), 40, (255, 255, 0))
        self.assertIsInstance(result, Image.Image)

    def test_returns_same_frame(self):
        result = draw_star(self.frame, (100, 100), 40, (255, 255, 0))
        self.assertIs(result, self.frame)

    def test_draws_color_near_center(self):
        frame = create_blank_frame(200, 200, color=(255, 255, 255))
        draw_star(frame, (100, 100), 40, (255, 0, 0))
        # The center pixel should be red (star covers center)
        self.assertEqual(frame.getpixel((100, 100)), (255, 0, 0))

    def test_with_outline_does_not_raise(self):
        draw_star(self.frame, (100, 100), 40, (255, 0, 0), outline_color=(0, 0, 0))

    def test_frame_size_unchanged(self):
        draw_star(self.frame, (100, 100), 40, (255, 255, 0))
        self.assertEqual(self.frame.size, (200, 200))


if __name__ == "__main__":
    unittest.main()
