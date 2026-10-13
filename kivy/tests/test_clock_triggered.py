import gc
from kivy.clock import triggered


class ClockCounter:
    def __init__(self):
        self.counter = 0
        self.last_args = None
        self.last_kwargs = None

    def __call__(self, *args, **kwargs):
        self.counter += 1
        self.last_args = args
        self.last_kwargs = kwargs


def test_triggered_global(kivy_clock):
    counter = ClockCounter()

    @triggered(0)
    def my_func(*args, **kwargs):
        counter(*args, **kwargs)

    # Trigger multiple times
    my_func(1, a="a")
    my_func(2, b="b")

    assert counter.counter == 0
    kivy_clock.tick()

    # Should be called once with the second call's arguments
    assert counter.counter == 1
    assert counter.last_args == (2,)
    assert counter.last_kwargs == {"b": "b"}


def test_triggered_instance_isolation(kivy_clock):
    class MyClass:
        def __init__(self, name):
            self.name = name
            self.counter = ClockCounter()

        @triggered(0)
        def my_method(self, *args, **kwargs):
            self.counter(*args, **kwargs)

    obj1 = MyClass("obj1")
    obj2 = MyClass("obj2")

    # Trigger both
    obj1.my_method(1)
    obj2.my_method(2)

    assert obj1.counter.counter == 0
    assert obj2.counter.counter == 0

    kivy_clock.tick()

    # Both should have been called independently
    assert obj1.counter.counter == 1
    assert obj1.counter.last_args == (1,)

    assert obj2.counter.counter == 1
    assert obj2.counter.last_args == (2,)


def test_triggered_instance_throttling(kivy_clock):
    class MyClass:
        def __init__(self):
            self.counter = ClockCounter()

        @triggered(0)
        def my_method(self, *args, **kwargs):
            self.counter(*args, **kwargs)

    obj = MyClass()

    # Trigger twice on same instance
    obj.my_method(1)
    obj.my_method(2)

    kivy_clock.tick()

    # Should be called once with second arguments
    assert obj.counter.counter == 1
    assert obj.counter.last_args == (2,)


def test_triggered_instance_cancel(kivy_clock):
    class MyClass:
        def __init__(self):
            self.counter = ClockCounter()

        @triggered(0)
        def my_method(self, *args, **kwargs):
            self.counter(*args, **kwargs)

    obj = MyClass()
    obj.my_method(1)
    obj.my_method.cancel()

    kivy_clock.tick()
    assert obj.counter.counter == 0


def test_triggered_memory_leak(kivy_clock):
    import weakref

    class MyClass:
        @triggered(0)
        def my_method(self):
            pass

    obj = MyClass()
    # Access the method to create the trigger entry in _instances
    method = obj.my_method

    obj_ref = weakref.ref(obj)

    # Check that obj is still alive
    assert obj_ref() is not None

    # Delete objective and trigger collection
    del obj
    del method
    gc.collect()

    # Object should be collected (meaning WeakKeyDictionary in TriggeredWrapper works)
    assert obj_ref() is None


def test_triggered_lazy_init(kivy_clock):
    # This is a bit internal but we can check if _trigger is None initially
    from kivy.clock import _TriggeredWrapper

    def my_func():
        pass

    wrapper = _TriggeredWrapper(my_func, 0, False, False)
    assert wrapper._trigger is None

    # Calling it should create the trigger
    wrapper()
    assert wrapper._trigger is not None


def test_triggered_debounce(kivy_clock_advance):
    counter = ClockCounter()

    @triggered(0.1, debounce=True)
    def my_func(val):
        counter(val)

    # Call 1: scheduled for +0.1s
    my_func(1)

    # Advance enough for debounce still pending (0.05 < 0.1)
    kivy_clock_advance(0.05)
    assert counter.counter == 0

    # Call 2: cancels Call 1 and reschedules for +0.1s from now
    my_func(2)

    # Advance enough to fire; should use args from Call 2
    kivy_clock_advance(0.15)

    assert counter.counter == 1
    assert counter.last_args == (2,)


def test_triggered_callable_as_timeout(kivy_clock):
    # Test @triggered without arguments (shorthand for @triggered())
    counter = ClockCounter()

    @triggered
    def my_func(dt):
        counter()

    my_func(0)
    kivy_clock.tick()
    assert counter.counter == 1


def test_triggered_is_triggered(kivy_clock_advance):
    results = []

    @triggered(0.1)
    def my_callback(val):
        results.append(val)

    # Global function
    assert not my_callback.is_triggered
    my_callback(1)
    assert my_callback.is_triggered

    # Advancing manually
    kivy_clock_advance(0.15)

    assert len(results) == 1
    assert not my_callback.is_triggered

    # Instance method
    class MyWidget:
        @triggered(0.1)
        def my_method(self, val):
            results.append((self, val))

    w = MyWidget()
    assert not w.my_method.is_triggered
    w.my_method(2)
    assert w.my_method.is_triggered

    kivy_clock_advance(0.15)

    assert len(results) == 2
    assert results[1] == (w, 2)
    assert not w.my_method.is_triggered

    # Test cancel
    w.my_method(3)
    assert w.my_method.is_triggered
    w.my_method.cancel()
    assert not w.my_method.is_triggered


def test_triggered_classmethod(kivy_clock_advance):
    results = []

    class MyClass:
        @classmethod
        @triggered(0.1)
        def my_classmethod(cls, val):
            results.append((cls, val))

    c1 = MyClass()
    c2 = MyClass()

    # Both instances and the class itself should share the SAME trigger
    c1.my_classmethod(1)
    assert c1.my_classmethod.is_triggered
    assert c2.my_classmethod.is_triggered # Shared!

    c2.my_classmethod(2) # Overwrites 1

    kivy_clock_advance(0.15)

    assert len(results) == 1
    assert results[0] == (MyClass, 2)


def test_triggered_staticmethod(kivy_clock_advance):
    results = []

    class MyClass:
        @staticmethod
        @triggered(0.1)
        def my_staticmethod(val):
            results.append(val)

    # All access points share the same trigger
    MyClass.my_staticmethod(1)
    obj = MyClass()
    assert obj.my_staticmethod.is_triggered

    obj.my_staticmethod(2)

    kivy_clock_advance(0.15)

    assert len(results) == 1
    assert results[0] == 2
