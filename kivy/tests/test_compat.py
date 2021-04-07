from kivy.compat import isclose


def test_isclose():
    assert isclose(1.1, 1.1), 'Close floats should assert True'
    assert not isclose(1.1, 2.1), 'Close floats should assert True'
