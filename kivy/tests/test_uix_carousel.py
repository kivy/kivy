import pytest


def test_remove_widget():
    from kivy.uix.carousel import Carousel
    from kivy.uix.widget import Widget

    c = Carousel()
    w = Widget()
    c.add_widget(w)
    assert len(c.children) == 1
    assert len(c.slides) == 1
    c.remove_widget(w)
    assert len(c.children) == 0
    assert len(c.slides) == 0
