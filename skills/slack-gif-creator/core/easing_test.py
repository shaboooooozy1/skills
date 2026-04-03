#!/usr/bin/env python3
"""Tests for easing.py"""

import unittest
import math

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


class TestEasingBoundaries(unittest.TestCase):
    """All easing functions must map 0->0 and 1->1."""

    FUNCTIONS = [
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

    def test_all_return_zero_at_zero(self):
        for fn in self.FUNCTIONS:
            with self.subTest(fn=fn.__name__):
                self.assertAlmostEqual(fn(0.0), 0.0, places=7)

    def test_all_return_one_at_one(self):
        for fn in self.FUNCTIONS:
            with self.subTest(fn=fn.__name__):
                self.assertAlmostEqual(fn(1.0), 1.0, places=7)


class TestLinear(unittest.TestCase):

    def test_midpoint(self):
        self.assertAlmostEqual(linear(0.5), 0.5)

    def test_quarter(self):
        self.assertAlmostEqual(linear(0.25), 0.25)


class TestQuadratic(unittest.TestCase):

    def test_ease_in_quad_midpoint(self):
        self.assertAlmostEqual(ease_in_quad(0.5), 0.25)

    def test_ease_out_quad_midpoint(self):
        self.assertAlmostEqual(ease_out_quad(0.5), 0.75)

    def test_ease_in_out_quad_midpoint(self):
        self.assertAlmostEqual(ease_in_out_quad(0.5), 0.5)

    def test_ease_in_out_quad_symmetry(self):
        self.assertAlmostEqual(
            ease_in_out_quad(0.25) + ease_in_out_quad(0.75), 1.0
        )


class TestCubic(unittest.TestCase):

    def test_ease_in_cubic_midpoint(self):
        self.assertAlmostEqual(ease_in_cubic(0.5), 0.125)

    def test_ease_out_cubic_midpoint(self):
        self.assertAlmostEqual(ease_out_cubic(0.5), 0.875)


class TestBounce(unittest.TestCase):

    def test_ease_out_bounce_midpoint_in_range(self):
        result = ease_out_bounce(0.5)
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_ease_in_bounce_relationship(self):
        # ease_in_bounce(t) == 1 - ease_out_bounce(1 - t)
        for t in [0.1, 0.3, 0.5, 0.7, 0.9]:
            with self.subTest(t=t):
                self.assertAlmostEqual(
                    ease_in_bounce(t), 1 - ease_out_bounce(1 - t)
                )

    def test_ease_in_out_bounce_symmetry(self):
        self.assertAlmostEqual(ease_in_out_bounce(0.5), 0.5, places=5)


class TestElastic(unittest.TestCase):

    def test_elastic_boundary_special_cases(self):
        # Elastic functions have explicit boundary checks
        self.assertEqual(ease_in_elastic(0), 0)
        self.assertEqual(ease_in_elastic(1), 1)
        self.assertEqual(ease_out_elastic(0), 0)
        self.assertEqual(ease_out_elastic(1), 1)

    def test_elastic_overshoots(self):
        # Elastic functions can overshoot beyond [0, 1]
        vals = [ease_out_elastic(t / 10.0) for t in range(1, 10)]
        self.assertTrue(any(v > 1.0 for v in vals) or any(v < 0.0 for v in vals))


class TestBackEasing(unittest.TestCase):

    def test_back_in_goes_negative(self):
        # Back ease-in overshoots backward (negative values)
        self.assertLess(ease_back_in(0.2), 0.0)

    def test_back_out_overshoots_one(self):
        # Back ease-out overshoots past 1.0
        self.assertGreater(ease_back_out(0.8), 1.0)


class TestGetEasing(unittest.TestCase):

    def test_known_names(self):
        for name in EASING_FUNCTIONS:
            with self.subTest(name=name):
                fn = get_easing(name)
                self.assertIs(fn, EASING_FUNCTIONS[name])

    def test_unknown_name_returns_linear(self):
        fn = get_easing("nonexistent")
        self.assertIs(fn, linear)

    def test_default_is_linear(self):
        fn = get_easing()
        self.assertIs(fn, linear)

    def test_aliases(self):
        self.assertIs(get_easing("anticipate"), ease_back_in)
        self.assertIs(get_easing("overshoot"), ease_back_out)


class TestInterpolate(unittest.TestCase):

    def test_linear_interpolation(self):
        self.assertAlmostEqual(interpolate(0, 100, 0.5), 50.0)

    def test_start_value(self):
        self.assertAlmostEqual(interpolate(10, 20, 0.0), 10.0)

    def test_end_value(self):
        self.assertAlmostEqual(interpolate(10, 20, 1.0), 20.0)

    def test_with_easing(self):
        result = interpolate(0, 100, 0.5, easing="ease_in")
        # ease_in_quad(0.5) = 0.25, so result should be 25
        self.assertAlmostEqual(result, 25.0)

    def test_reverse_range(self):
        self.assertAlmostEqual(interpolate(100, 0, 0.5), 50.0)


class TestApplySquashStretch(unittest.TestCase):

    def test_vertical_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "vertical")
        self.assertGreater(w, 1.0)  # expands horizontally
        self.assertLess(h, 1.0)  # compresses vertically

    def test_horizontal_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "horizontal")
        self.assertLess(w, 1.0)  # compresses horizontally
        self.assertGreater(h, 1.0)  # expands vertically

    def test_both_direction(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "both")
        self.assertLess(w, 1.0)
        self.assertLess(h, 1.0)

    def test_zero_intensity_unchanged(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.0, "vertical")
        self.assertAlmostEqual(w, 1.0)
        self.assertAlmostEqual(h, 1.0)

    def test_unknown_direction_unchanged(self):
        w, h = apply_squash_stretch((1.0, 1.0), 1.0, "diagonal")
        self.assertAlmostEqual(w, 1.0)
        self.assertAlmostEqual(h, 1.0)


class TestCalculateArcMotion(unittest.TestCase):

    def test_start_position(self):
        x, y = calculate_arc_motion((0, 0), (100, 100), 50, 0.0)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 0.0)

    def test_end_position(self):
        x, y = calculate_arc_motion((0, 0), (100, 100), 50, 1.0)
        self.assertAlmostEqual(x, 100.0)
        self.assertAlmostEqual(y, 100.0)

    def test_midpoint_x_is_linear(self):
        x, y = calculate_arc_motion((0, 0), (100, 0), 50, 0.5)
        self.assertAlmostEqual(x, 50.0)

    def test_midpoint_arc_offset(self):
        # At t=0.5, arc_offset = 4 * height * 0.5 * 0.5 = height
        x, y = calculate_arc_motion((0, 0), (0, 0), 50, 0.5)
        self.assertAlmostEqual(y, -50.0)  # offset is subtracted

    def test_zero_height_is_linear(self):
        x, y = calculate_arc_motion((0, 0), (100, 100), 0, 0.5)
        self.assertAlmostEqual(x, 50.0)
        self.assertAlmostEqual(y, 50.0)


if __name__ == "__main__":
    unittest.main()
