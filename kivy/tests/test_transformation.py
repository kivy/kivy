from math import pi, sqrt

import pytest

from kivy.graphics.transformation import Matrix


def approx(values):
    return pytest.approx(values, abs=1e-9)


def test_transforms_of_the_identity_are_unchanged():
    assert Matrix().translate(1, 2, 3).get() == (
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 3, 1)
    assert Matrix().scale(2, 3, 4).get() == (
        2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 4, 0, 0, 0, 0, 1)
    assert Matrix().rotate(pi / 2, 0, 0, 1).get() == approx(
        (0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))


def test_chained_transforms_apply_in_call_order():
    # translate, then rotate (the example from issue #4638)
    m = Matrix().translate(-5, -5, 0).rotate(pi / 4, 0, 0, 1)
    assert m.transform_point(7, 7, 0) == approx((0, 2 * sqrt(2), 0))
    # rotate, then translate
    m = Matrix().rotate(pi / 4, 0, 0, 1).translate(-5, -5, 0)
    assert m.transform_point(7, 7, 0) == approx((-5, 7 * sqrt(2) - 5, 0))
    # translate, then scale
    m = Matrix().translate(1, 0, 0).scale(2, 2, 2)
    assert m.transform_point(0, 0, 0) == approx((2, 0, 0))
    # rotate, then scale
    m = Matrix().rotate(pi / 4, 0, 0, 1).scale(2, 1, 1)
    assert m.transform_point(1, 1, 0) == approx((0, sqrt(2), 0))


@pytest.mark.parametrize('transform', [
    lambda m: m.rotate(0.3, 1, 2, 3),
    lambda m: m.scale(2, 3, 4),
    lambda m: m.translate(1, 2, 3),
])
def test_transform_is_applied_after_the_matrix(transform):
    m = Matrix().rotate(0.5, 0, 1, 0).translate(4, 5, 6).scale(1, 2, 3)
    expected = transform(Matrix()).multiply(m)
    assert transform(m).get() == approx(expected.get())
