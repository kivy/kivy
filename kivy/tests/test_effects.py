def test_expand_the_capacity_of_the_history(kivy_clock):
    from kivy.effects.kinetic import KineticEffect
    e = KineticEffect(max_history=3)
    e.start(10, 1)
    for i in range(2, 7):
        e.update(i * 10, i)
    assert list(e.history) == [(4, 40), (5, 50), (6, 60)]
    e.max_history = 5
    assert list(e.history) == [(4, 40), (5, 50), (6, 60)]


def test_shrink_the_capacity_of_the_history(kivy_clock):
    from kivy.effects.kinetic import KineticEffect
    e = KineticEffect(max_history=3)
    e.start(10, 1)
    for i in range(2, 7):
        e.update(i * 10, i)
    assert list(e.history) == [(4, 40), (5, 50), (6, 60)]
    e.max_history = 2
    assert list(e.history) == [(5, 50), (6, 60)]


def test_ScrollEffect_reset(kivy_clock):
    from kivy.effects.scroll import ScrollEffect
    e = ScrollEffect(value=11, velocity=22, max=100, min=-100)
    e.start(10, 1)
    e.update(20, 2)
    assert list(e.history) == [(1, 10), (2, 20)]
    e.reset(33)
    assert e.value == 33
    assert e.velocity == 0

    # ??? is the time 'reset()' was called, no point of testing it
    # assert list(e.history) == [(???, 20)]

    assert len(e.history) == 1
    assert e.history[0][1] == 20
