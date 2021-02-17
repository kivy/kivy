import pytest


@pytest.mark.parametrize('unit', ['inch', 'dp', 'sp', 'pt', 'cm', 'mm'])
def test_metrics_scale_factors(kivy_metrics, unit):
    from kivy.metrics import dpi2px
    import kivy.metrics as m
    kivy_metrics.density = 2
    kivy_metrics.dpi = 101
    kivy_metrics.fontscale = 3

    factor = getattr(kivy_metrics, unit)
    print(kivy_metrics.fontscale)
    assert pytest.approx(7 * factor) == dpi2px(7, unit[:2])  # inch -> in
    assert pytest.approx(7 * factor) == getattr(m, unit)(7)

    kivy_metrics.density = 5
    kivy_metrics.dpi = 103
    kivy_metrics.fontscale = 11

    new_factor = getattr(kivy_metrics, unit)
    assert new_factor != pytest.approx(factor)
    assert pytest.approx(7 * new_factor) == dpi2px(7, unit[:2])
    assert pytest.approx(7 * new_factor) == getattr(m, unit)(7)
    assert pytest.approx(7 * factor) != dpi2px(7, unit[:2])
    assert pytest.approx(7 * factor) != getattr(m, unit)(7)

    # assert pytest.approx(10 * new_factor) == dpi2px(10, unit)
    assert pytest.approx(100 * new_factor) == dpi2px(100, unit[:2])
    assert pytest.approx(1000 * new_factor) == dpi2px(1000, unit[:2])
