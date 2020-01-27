import pytest


@pytest.fixture(
    scope='session', params=(True, False), ids=lambda v: 'loop=' + str(v))
def loop(request):
    return request.param


def test_remove_widget(loop):
    from kivy.uix.carousel import Carousel
    from kivy.uix.widget import Widget

    c = Carousel(loop=loop)
    assert c.index is None
    assert c.current_slide is None
    assert len(c.children) == 0
    assert len(c.slides) == 0

    N_SLIDES = 4
    for i in range(N_SLIDES):
        c.add_widget(Widget())
    assert c.index == 0
    assert c.current_slide == c.slides[0]
    assert len(c.children) == 3 if loop else 2
    assert len(c.slides) == N_SLIDES

    # test issue #6370
    c.index = len(c.slides) - 1
    c.remove_widget(c.slides[0])

    # remove a slide(smaller index than the current_slide's).
    c.index = 1
    old_current_slide = c.current_slide
    c.remove_widget(c.slides[c.index - 1])
    assert c.index == 0
    assert c.current_slide is old_current_slide
    assert len(c.children) == 2
    assert len(c.slides) == 2

    # remove a slide(bigger index than the current_slide's).
    old_current_slide = c.current_slide
    c.remove_widget(c.slides[c.index + 1])
    assert c.index == 0
    assert c.current_slide is old_current_slide
    assert len(c.children) == 1
    assert len(c.slides) == 1

    # remove the current_slide(the last one left).
    c.remove_widget(c.current_slide)
    assert c.index is None
    assert c.current_slide is None
    assert len(c.children) == 0
    assert len(c.slides) == 0


@pytest.mark.parametrize(
    ('n_slides', 'index', 'loop',
    'index_of_previous_slide', 'index_of_next_slide'),
    (
        (1, 0, False, None, None),
        (1, 0, True, None, None),
        (2, 0, False, None, 1),
        (2, 0, True, 1, 1),
        (2, 1, False, 0, None),
        (2, 1, True, 0, 0),
        (3, 0, False, None, 1),
        (3, 0, True, 2, 1),
        (3, 1, False, 0, 2),
        (3, 1, True, 0, 2),
        (3, 2, False, 1, None),
        (3, 2, True, 1, 0),
    )
)
def test_previous_and_next(
    n_slides, index, loop, index_of_previous_slide, index_of_next_slide
):
    from kivy.uix.carousel import Carousel
    from kivy.uix.widget import Widget
    c = Carousel(loop=loop)
    for i in range(n_slides):
        c.add_widget(Widget())
    c.index = index
    p_slide = c.previous_slide
    assert (p_slide and c.slides.index(p_slide)) == index_of_previous_slide
    n_slide = c.next_slide
    assert (n_slide and c.slides.index(n_slide)) == index_of_next_slide


if __name__ == "__main__":
    pytest.main(args=[
        __file__,
    ])
