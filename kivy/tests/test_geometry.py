import pytest

from kivy.geometry import circumcircle, minimum_bounding_circle


def test_circumcircle_rejects_collinear_and_coincident_points():
    for points in (
        ((0, 0), (1, 1), (2, 2)),
        ((0, 0), (0, 0), (0, 0)),
    ):
        with pytest.raises(ValueError, match="collinear or coincident"):
            circumcircle(*points)


def test_circumcircle_for_non_degenerate_points():
    center, radius = circumcircle((0, 0), (1, 0), (0, 1))

    assert center == pytest.approx((0.5, 0.5))
    assert radius == pytest.approx(2**0.5 / 2)


def test_minimum_bounding_circle_for_non_degenerate_points():
    center, radius = minimum_bounding_circle([(0, 0), (1, 0), (0, 1)])

    assert center == pytest.approx((0.5, 0.5))
    assert radius == pytest.approx(2**0.5 / 2)
