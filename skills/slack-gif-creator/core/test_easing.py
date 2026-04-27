#!/usr/bin/env python3
"""
Tests for easing.py - easing functions, interpolation, and motion utilities.
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from easing import (
    linear,
    ease_in_quad,
    ease_out_quad,
    ease_in_out_quad,
    ease_in_cubic,
    ease_out_cubic,
    ease_in_out_cubic,
    ease_in_bounce,
    ease_out_bounce,
    ease_in_out_bounce,
    ease_in_elastic,
    ease_out_elastic,
    ease_in_out_elastic,
    ease_back_in,
    ease_back_out,
    ease_back_in_out,
    get_easing,
    interpolate,
    apply_squash_stretch,
    calculate_arc_motion,
    EASING_FUNCTIONS,
)

# Explicit list is intentional: ease_in_cubic, ease_out_cubic, and ease_in_out_cubic
# are not registered in EASING_FUNCTIONS, so we cannot rely on EASING_FUNCTIONS.values()
# to cover all implementations.
BOUNDARY_FUNCS = [
    linear,
    ease_in_quad,
    ease_out_quad,
    ease_in_out_quad,
    ease_in_cubic,
    ease_out_cubic,
    ease_in_out_cubic,
    ease_in_bounce,
    ease_out_bounce,
    ease_in_out_bounce,
    ease_in_elastic,
    ease_out_elastic,
    ease_in_out_elastic,
    ease_back_in,
    ease_back_out,
    ease_back_in_out,
]


class TestBoundaryValues(unittest.TestCase):
    """All easing functions must map 0→0 and 1→1."""

    def _assert_boundary(self, func):
        self.assertAlmostEqual(func(0.0), 0.0, places=6,
                               msg=f"{func.__name__}(0) != 0")
        self.assertAlmostEqual(func(1.0), 1.0, places=6,
                               msg=f"{func.__name__}(1) != 1")

    def test_all_boundary_values(self):
        for func in BOUNDARY_FUNCS:
            with self.subTest(func=func.__name__):
                self._assert_boundary(func)


class TestLinear(unittest.TestCase):

    def test_midpoint(self):
        self.assertAlmostEqual(linear(0.5), 0.5)

    def test_quarter(self):
        self.assertAlmostEqual(linear(0.25), 0.25)

    def test_identity(self):
        for t in [0.0, 0.1, 0.5, 0.9, 1.0]:
            self.assertAlmostEqual(linear(t), t)


class TestEaseInQuad(unittest.TestCase):

    def test_slow_start(self):
        # ease-in: value at t=0.5 should be < 0.5 (still accelerating)
        self.assertLess(ease_in_quad(0.5), 0.5)

    def test_is_monotone(self):
        prev = ease_in_quad(0.0)
        for i in range(1, 11):
            curr = ease_in_quad(i / 10)
            self.assertGreaterEqual(curr, prev)
            prev = curr


class TestEaseOutQuad(unittest.TestCase):

    def test_fast_start(self):
        # ease-out: value at t=0.5 should be > 0.5 (already decelerating)
        self.assertGreater(ease_out_quad(0.5), 0.5)

    def test_is_monotone(self):
        prev = ease_out_quad(0.0)
        for i in range(1, 11):
            curr = ease_out_quad(i / 10)
            self.assertGreaterEqual(curr, prev)
            prev = curr


class TestEaseInOutQuad(unittest.TestCase):

    def test_midpoint(self):
        self.assertAlmostEqual(ease_in_out_quad(0.5), 0.5)

    def test_slow_at_ends_fast_in_middle(self):
        # First quarter should be below linear
        self.assertLess(ease_in_out_quad(0.25), 0.25)
        # Third quarter should be above linear
        self.assertGreater(ease_in_out_quad(0.75), 0.75)


class TestEaseInCubic(unittest.TestCase):

    def test_slower_than_quad_at_midpoint(self):
        self.assertLess(ease_in_cubic(0.5), ease_in_quad(0.5))


class TestEaseOutCubic(unittest.TestCase):

    def test_faster_than_quad_at_midpoint(self):
        self.assertGreater(ease_out_cubic(0.5), ease_out_quad(0.5))


class TestEaseInOutCubic(unittest.TestCase):

    def test_midpoint(self):
        self.assertAlmostEqual(ease_in_out_cubic(0.5), 0.5)


class TestEaseOutBounce(unittest.TestCase):

    def test_segments(self):
        # Each segment should return a value between 0 and 1
        for t in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            val = ease_out_bounce(t)
            self.assertGreaterEqual(val, 0.0, f"t={t}")
            self.assertLessEqual(val, 1.0 + 1e-9, f"t={t}")


class TestEaseInBounce(unittest.TestCase):

    def test_complement_relationship(self):
        # ease_in_bounce(t) should equal 1 - ease_out_bounce(1 - t)
        for t in [0.1, 0.3, 0.5, 0.7, 0.9]:
            expected = 1.0 - ease_out_bounce(1.0 - t)
            self.assertAlmostEqual(ease_in_bounce(t), expected, places=9)


class TestElasticFunctions(unittest.TestCase):

    def test_elastic_in_boundary(self):
        self.assertAlmostEqual(ease_in_elastic(0), 0)
        self.assertAlmostEqual(ease_in_elastic(1), 1)

    def test_elastic_out_boundary(self):
        self.assertAlmostEqual(ease_out_elastic(0), 0)
        self.assertAlmostEqual(ease_out_elastic(1), 1)

    def test_elastic_in_out_boundary(self):
        self.assertAlmostEqual(ease_in_out_elastic(0), 0)
        self.assertAlmostEqual(ease_in_out_elastic(1), 1)

    def test_elastic_in_out_midpoint(self):
        # Should be symmetric around midpoint
        self.assertAlmostEqual(ease_in_out_elastic(0.5), 0.5, places=5)


class TestGetEasing(unittest.TestCase):

    def test_known_name_returns_correct_function(self):
        func = get_easing("linear")
        self.assertIs(func, linear)

    def test_ease_in_alias(self):
        func = get_easing("ease_in")
        self.assertIs(func, ease_in_quad)

    def test_ease_out_alias(self):
        func = get_easing("ease_out")
        self.assertIs(func, ease_out_quad)

    def test_unknown_name_returns_linear(self):
        func = get_easing("nonexistent_easing_xyz")
        self.assertIs(func, linear)

    def test_default_is_linear(self):
        func = get_easing()
        self.assertIs(func, linear)

    def test_all_registered_functions_callable(self):
        for name, func in EASING_FUNCTIONS.items():
            with self.subTest(name=name):
                self.assertTrue(callable(func))
                result = func(0.5)
                self.assertIsInstance(result, float)


class TestInterpolate(unittest.TestCase):

    def test_at_t0_returns_start(self):
        self.assertAlmostEqual(interpolate(10, 20, 0.0), 10.0)

    def test_at_t1_returns_end(self):
        self.assertAlmostEqual(interpolate(10, 20, 1.0), 20.0)

    def test_linear_midpoint(self):
        self.assertAlmostEqual(interpolate(0, 100, 0.5, "linear"), 50.0)

    def test_with_non_default_easing(self):
        # ease_in_quad(0.5) = 0.25, so result = 0 + (100 - 0) * 0.25 = 25
        result = interpolate(0, 100, 0.5, "ease_in")
        self.assertAlmostEqual(result, 25.0)

    def test_negative_range(self):
        result = interpolate(-10, 10, 0.5, "linear")
        self.assertAlmostEqual(result, 0.0)

    def test_reversed_range(self):
        result = interpolate(100, 0, 0.5, "linear")
        self.assertAlmostEqual(result, 50.0)


class TestCalculateArcMotion(unittest.TestCase):

    def test_at_t0_returns_start(self):
        start = (0.0, 0.0)
        end = (100.0, 0.0)
        x, y = calculate_arc_motion(start, end, 50.0, 0.0)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 0.0)

    def test_at_t1_returns_end(self):
        start = (0.0, 0.0)
        end = (100.0, 50.0)
        x, y = calculate_arc_motion(start, end, 30.0, 1.0)
        self.assertAlmostEqual(x, 100.0)
        self.assertAlmostEqual(y, 50.0)

    def test_arc_peaks_at_midpoint(self):
        start = (0.0, 0.0)
        end = (100.0, 0.0)
        height = 40.0
        _, y_mid = calculate_arc_motion(start, end, height, 0.5)
        # At t=0.5, arc_offset = 4 * height * 0.5 * 0.5 = height
        # y = 0 + (0 - 0) * 0.5 - height = -height
        self.assertAlmostEqual(y_mid, -height)

    def test_x_is_linear(self):
        start = (0.0, 0.0)
        end = (200.0, 0.0)
        x, _ = calculate_arc_motion(start, end, 0.0, 0.5)
        self.assertAlmostEqual(x, 100.0)

    def test_zero_height_is_linear_path(self):
        start = (0.0, 10.0)
        end = (100.0, 20.0)
        x, y = calculate_arc_motion(start, end, 0.0, 0.5)
        self.assertAlmostEqual(x, 50.0)
        self.assertAlmostEqual(y, 15.0)


class TestApplySquashStretch(unittest.TestCase):

    def test_vertical_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.5, "vertical")
        # Vertical squash: height decreases, width increases
        self.assertLess(h, 1.0)
        self.assertGreater(w, 1.0)

    def test_horizontal_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.5, "horizontal")
        self.assertLess(w, 1.0)
        self.assertGreater(h, 1.0)

    def test_both_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.5, "both")
        self.assertLess(w, 1.0)
        self.assertLess(h, 1.0)

    def test_zero_intensity_unchanged(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.0, "vertical")
        self.assertAlmostEqual(w, 1.0)
        self.assertAlmostEqual(h, 1.0)

    def test_unknown_direction_unchanged(self):
        w, h = apply_squash_stretch((2.0, 3.0), 0.5, "unknown")
        self.assertAlmostEqual(w, 2.0)
        self.assertAlmostEqual(h, 3.0)

    def test_non_unit_base_scale(self):
        w, h = apply_squash_stretch((2.0, 2.0), 0.5, "vertical")
        self.assertAlmostEqual(h, 2.0 * (1 - 0.5 * 0.5))
        self.assertAlmostEqual(w, 2.0 * (1 + 0.5 * 0.5))


if __name__ == "__main__":
    unittest.main()
