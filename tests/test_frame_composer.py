"""
Tests for slack-gif-creator/core/frame_composer.py
"""

import pytest
import numpy as np

try:
    from PIL import Image
    from frame_composer import (
        create_blank_frame,
        draw_circle,
        draw_text,
        create_gradient_background,
        draw_star,
    )
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PIL_AVAILABLE, reason="Pillow not installed")


class TestCreateBlankFrame:
    def test_returns_pil_image(self):
        frame = create_blank_frame(100, 100)
        assert isinstance(frame, Image.Image)

    def test_correct_dimensions(self):
        frame = create_blank_frame(200, 150)
        assert frame.size == (200, 150)

    def test_default_color_is_white(self):
        frame = create_blank_frame(10, 10)
        arr = np.array(frame)
        assert np.all(arr == 255)

    def test_custom_color(self):
        frame = create_blank_frame(10, 10, color=(0, 0, 0))
        arr = np.array(frame)
        assert np.all(arr == 0)

    def test_rgb_mode(self):
        frame = create_blank_frame(10, 10)
        assert frame.mode == "RGB"


class TestDrawCircle:
    def test_returns_image(self):
        frame = create_blank_frame(100, 100)
        result = draw_circle(frame, (50, 50), 20, fill_color=(255, 0, 0))
        assert isinstance(result, Image.Image)

    def test_modifies_frame_in_place(self):
        frame = create_blank_frame(100, 100, color=(255, 255, 255))
        result = draw_circle(frame, (50, 50), 20, fill_color=(255, 0, 0))
        # Result should be the same object (modified in place)
        assert result is frame

    def test_pixels_changed_at_center(self):
        frame = create_blank_frame(100, 100, color=(255, 255, 255))
        draw_circle(frame, (50, 50), 20, fill_color=(255, 0, 0))
        # Center pixel should now be red
        center_pixel = frame.getpixel((50, 50))
        assert center_pixel == (255, 0, 0)

    def test_with_outline(self):
        frame = create_blank_frame(100, 100, color=(255, 255, 255))
        result = draw_circle(frame, (50, 50), 20, outline_color=(0, 0, 0))
        assert isinstance(result, Image.Image)

    def test_no_fill_no_outline(self):
        # Should not raise
        frame = create_blank_frame(100, 100)
        result = draw_circle(frame, (50, 50), 20)
        assert isinstance(result, Image.Image)


class TestDrawText:
    def test_returns_image(self):
        frame = create_blank_frame(200, 100)
        result = draw_text(frame, "Hello", (10, 10))
        assert isinstance(result, Image.Image)

    def test_modifies_frame(self):
        frame = create_blank_frame(200, 100, color=(255, 255, 255))
        result = draw_text(frame, "X", (10, 10), color=(0, 0, 0))
        # Some pixel near the draw position should have changed
        arr_before = np.array(create_blank_frame(200, 100, color=(255, 255, 255)))
        arr_after = np.array(result)
        assert not np.array_equal(arr_before, arr_after)

    def test_centered_text(self):
        frame = create_blank_frame(200, 100)
        result = draw_text(frame, "Hello", (100, 50), centered=True)
        assert isinstance(result, Image.Image)

    def test_custom_color(self):
        frame = create_blank_frame(200, 100, color=(255, 255, 255))
        draw_text(frame, "A", (5, 5), color=(255, 0, 0))
        # At least one pixel around (5,5) should be red-ish
        arr = np.array(frame)
        region = arr[0:20, 0:20]
        # Some pixel with high red component
        assert np.any(region[:, :, 0] > 200)

    def test_empty_string(self):
        frame = create_blank_frame(100, 100)
        result = draw_text(frame, "", (10, 10))
        assert isinstance(result, Image.Image)


class TestCreateGradientBackground:
    def test_returns_image(self):
        frame = create_gradient_background(100, 100, (255, 0, 0), (0, 0, 255))
        assert isinstance(frame, Image.Image)

    def test_correct_dimensions(self):
        frame = create_gradient_background(200, 150, (255, 0, 0), (0, 0, 255))
        assert frame.size == (200, 150)

    def test_top_color_at_top(self):
        top = (255, 0, 0)
        bottom = (0, 0, 255)
        frame = create_gradient_background(10, 100, top, bottom)
        top_pixel = frame.getpixel((5, 0))
        assert top_pixel == top

    def test_bottom_color_at_bottom(self):
        top = (255, 0, 0)
        bottom = (0, 0, 255)
        frame = create_gradient_background(10, 100, top, bottom)
        # Last row should be approximately blue
        bottom_pixel = frame.getpixel((5, 99))
        # The ratio at y=99 is 99/100 = 0.99, so it's very close to bottom
        assert bottom_pixel[2] > 200  # high blue channel

    def test_gradient_changes_vertically(self):
        frame = create_gradient_background(10, 10, (255, 0, 0), (0, 0, 255))
        arr = np.array(frame)
        # Red channel should decrease from top to bottom
        assert arr[0, 0, 0] > arr[9, 0, 0]
        # Blue channel should increase
        assert arr[0, 0, 2] < arr[9, 0, 2]

    def test_same_color_both_ends_is_solid(self):
        color = (128, 64, 32)
        frame = create_gradient_background(10, 10, color, color)
        arr = np.array(frame)
        assert np.all(arr == np.array(color, dtype=np.uint8))


class TestDrawStar:
    def test_returns_image(self):
        frame = create_blank_frame(100, 100)
        result = draw_star(frame, (50, 50), 20, (255, 255, 0))
        assert isinstance(result, Image.Image)

    def test_modifies_frame(self):
        frame = create_blank_frame(100, 100, color=(255, 255, 255))
        draw_star(frame, (50, 50), 20, (0, 0, 0))
        arr = np.array(frame)
        # Some non-white pixels should exist
        assert np.any(arr < 255)

    def test_with_outline(self):
        frame = create_blank_frame(100, 100)
        result = draw_star(frame, (50, 50), 20, (255, 0, 0), outline_color=(0, 0, 0))
        assert isinstance(result, Image.Image)

    def test_center_pixel_is_fill_color(self):
        frame = create_blank_frame(200, 200, color=(255, 255, 255))
        fill = (0, 128, 0)
        draw_star(frame, (100, 100), 30, fill)
        center = frame.getpixel((100, 100))
        assert center == fill

    def test_does_not_raise_for_small_size(self):
        frame = create_blank_frame(50, 50)
        draw_star(frame, (25, 25), 5, (255, 0, 0))
