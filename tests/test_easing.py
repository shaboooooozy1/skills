"""
Tests for slack-gif-creator/core/easing.py
"""

import math
import pytest

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


# ---------------------------------------------------------------------------
# Helper: all easing functions must map 0→0 and 1→1 (endpoints invariant)
# ---------------------------------------------------------------------------

ENDPOINT_FUNCS = [
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


@pytest.mark.parametrize("fn", ENDPOINT_FUNCS)
def test_easing_endpoints_zero(fn):
    assert fn(0.0) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("fn", ENDPOINT_FUNCS)
def test_easing_endpoints_one(fn):
    assert fn(1.0) == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Individual easing function correctness
# ---------------------------------------------------------------------------

class TestLinear:
    def test_midpoint(self):
        assert linear(0.5) == pytest.approx(0.5)

    def test_quarter(self):
        assert linear(0.25) == pytest.approx(0.25)


class TestEaseInQuad:
    def test_midpoint_less_than_linear(self):
        # Ease-in is slow at start, so midpoint value < 0.5
        assert ease_in_quad(0.5) < 0.5

    def test_value(self):
        assert ease_in_quad(0.5) == pytest.approx(0.25)


class TestEaseOutQuad:
    def test_midpoint_greater_than_linear(self):
        # Ease-out is fast at start, so midpoint value > 0.5
        assert ease_out_quad(0.5) > 0.5

    def test_value(self):
        assert ease_out_quad(0.5) == pytest.approx(0.75)


class TestEaseInOutQuad:
    def test_midpoint_equals_half(self):
        assert ease_in_out_quad(0.5) == pytest.approx(0.5)

    def test_symmetric(self):
        # ease_in_out should be symmetric: f(t) + f(1-t) == 1
        for t in [0.1, 0.25, 0.4, 0.75]:
            assert ease_in_out_quad(t) + ease_in_out_quad(1 - t) == pytest.approx(1.0)


class TestEaseInCubic:
    def test_value(self):
        assert ease_in_cubic(0.5) == pytest.approx(0.125)

    def test_slower_than_quad(self):
        assert ease_in_cubic(0.5) < ease_in_quad(0.5)


class TestEaseOutCubic:
    def test_value(self):
        assert ease_out_cubic(0.5) == pytest.approx(0.875)


class TestEaseInOutCubic:
    def test_midpoint(self):
        assert ease_in_out_cubic(0.5) == pytest.approx(0.5)


class TestEaseBounce:
    def test_out_bounce_midpoint_in_range(self):
        v = ease_out_bounce(0.5)
        assert 0.0 <= v <= 1.0

    def test_in_bounce_complement(self):
        # ease_in_bounce(t) == 1 - ease_out_bounce(1 - t)
        for t in [0.1, 0.3, 0.5, 0.7, 0.9]:
            assert ease_in_bounce(t) == pytest.approx(1 - ease_out_bounce(1 - t))

    def test_in_out_bounce_midpoint(self):
        assert ease_in_out_bounce(0.5) == pytest.approx(0.5)

    def test_out_bounce_all_segments(self):
        # Exercise all four branches of ease_out_bounce
        vals = [ease_out_bounce(t) for t in [0.1, 0.5, 0.8, 0.95]]
        for v in vals:
            assert 0.0 <= v <= 1.05  # slight overshoot allowed


class TestEaseElastic:
    def test_in_elastic_boundary_zero(self):
        assert ease_in_elastic(0) == 0.0

    def test_in_elastic_boundary_one(self):
        assert ease_in_elastic(1) == 1.0

    def test_out_elastic_boundary_zero(self):
        assert ease_out_elastic(0) == 0.0

    def test_out_elastic_boundary_one(self):
        assert ease_out_elastic(1) == 1.0

    def test_in_out_elastic_midpoint(self):
        assert ease_in_out_elastic(0.5) == pytest.approx(0.5, abs=1e-9)

    def test_in_out_elastic_boundaries(self):
        assert ease_in_out_elastic(0) == 0.0
        assert ease_in_out_elastic(1) == 1.0


class TestEaseBack:
    def test_back_in_goes_negative(self):
        # ease_back_in overshoots backward slightly before t=0.5
        assert ease_back_in(0.3) < 0.0

    def test_back_out_goes_above_one(self):
        # ease_back_out overshoots beyond 1 slightly before settling
        assert ease_back_out(0.7) > 1.0

    def test_back_in_out_midpoint(self):
        assert ease_back_in_out(0.5) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# get_easing
# ---------------------------------------------------------------------------

class TestGetEasing:
    def test_known_name_returns_function(self):
        fn = get_easing("linear")
        assert callable(fn)
        assert fn(0.5) == pytest.approx(0.5)

    def test_unknown_name_returns_linear(self):
        fn = get_easing("nonexistent")
        assert fn is linear

    def test_all_registered_names_callable(self):
        for name, fn in EASING_FUNCTIONS.items():
            assert callable(fn), f"{name} is not callable"

    def test_default_argument_is_linear(self):
        fn = get_easing()
        assert fn is linear


# ---------------------------------------------------------------------------
# interpolate
# ---------------------------------------------------------------------------

class TestInterpolate:
    def test_linear_midpoint(self):
        assert interpolate(0, 100, 0.5) == pytest.approx(50.0)

    def test_at_zero(self):
        assert interpolate(10, 90, 0.0) == pytest.approx(10.0)

    def test_at_one(self):
        assert interpolate(10, 90, 1.0) == pytest.approx(90.0)

    def test_with_easing(self):
        result = interpolate(0, 100, 0.5, easing="ease_in")
        # ease_in_quad(0.5) = 0.25 → value should be 25
        assert result == pytest.approx(25.0)

    def test_negative_range(self):
        assert interpolate(-100, 0, 0.5) == pytest.approx(-50.0)

    def test_reversed_range(self):
        assert interpolate(100, 0, 0.5) == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# apply_squash_stretch
# ---------------------------------------------------------------------------

class TestApplySquashStretch:
    def test_vertical_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.5, direction="vertical")
        assert h < 1.0
        assert w > 1.0

    def test_horizontal_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.5, direction="horizontal")
        assert w < 1.0
        assert h > 1.0

    def test_both_squash(self):
        w, h = apply_squash_stretch((1.0, 1.0), 0.5, direction="both")
        assert w < 1.0
        assert h < 1.0

    def test_zero_intensity_no_change(self):
        base = (1.5, 2.0)
        w, h = apply_squash_stretch(base, 0.0, direction="vertical")
        assert (w, h) == base

    def test_unknown_direction_no_change(self):
        base = (1.0, 1.0)
        result = apply_squash_stretch(base, 0.5, direction="diagonal")
        assert result == base

    def test_returns_tuple(self):
        result = apply_squash_stretch((1.0, 1.0), 0.5)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# calculate_arc_motion
# ---------------------------------------------------------------------------

class TestCalculateArcMotion:
    def test_at_start(self):
        x, y = calculate_arc_motion((0, 0), (100, 100), height=50, t=0.0)
        assert x == pytest.approx(0.0)
        assert y == pytest.approx(0.0)

    def test_at_end(self):
        x, y = calculate_arc_motion((0, 0), (100, 100), height=50, t=1.0)
        assert x == pytest.approx(100.0)
        assert y == pytest.approx(100.0)

    def test_midpoint_x_is_halfway(self):
        x, y = calculate_arc_motion((0, 0), (100, 0), height=50, t=0.5)
        assert x == pytest.approx(50.0)

    def test_midpoint_y_arcs_upward(self):
        # height > 0 means upward arc; at midpoint arc_offset = 4*height*0.5*0.5 = height
        x, y = calculate_arc_motion((0, 0), (0, 0), height=50, t=0.5)
        # arc_offset = 4 * 50 * 0.5 * 0.5 = 50; y = 0 - 50 = -50
        assert y == pytest.approx(-50.0)

    def test_linear_x_interpolation(self):
        for t in [0.25, 0.5, 0.75]:
            x, _ = calculate_arc_motion((0, 0), (200, 0), height=0, t=t)
            assert x == pytest.approx(200 * t)

    def test_returns_tuple_of_two(self):
        result = calculate_arc_motion((0, 0), (1, 1), height=10, t=0.5)
        assert isinstance(result, tuple)
        assert len(result) == 2
