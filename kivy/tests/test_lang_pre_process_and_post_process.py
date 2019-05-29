import unittest
import textwrap
from collections import defaultdict


class TrackCallbacks(object):

    kv_pre_events = []
    '''Stores values added during the pre event dispatched callbacks.
    '''

    kv_applied_events = []
    '''Stores values added during the applied event dispatched callbacks.
    '''

    kv_post_events = []
    '''Stores values added during the post event dispatched callbacks.
    '''

    events_in_pre = []
    '''List of expected events that should be in kv_pre_events after all the
    callbacks has been executed.
    '''

    events_in_applied = []
    '''List of expected events that should be in kv_applied_events after all
    the callbacks has been executed.
    '''

    events_in_post = []
    '''List of expected events that should be in kv_post_events after all the
    callbacks has been executed.
    '''

    instantiated_widgets = []
    '''Whenever a widget of this class is instantiated, it is added to this
    list, which is class specific.

    It lets us iterate through all the instance of this class and assert for
    all of them as needed.
    '''

    root_widget = None
    '''The expected root widget in the kv rule as dispatched in on_kv_applied.
    '''

    base_widget = None
    '''The expected base widget as dispatched in on_kv_post.
    '''

    actual_root_widget = None
    '''The actual root widget in the kv rule as dispatched in on_kv_applied.
    '''

    actual_base_widget = None
    '''The actual base widget as dispatched in on_kv_post.
    '''

    name = 'none'
    '''Optional name given to the widget to help it identify during a test
    failure.
    '''

    my_roots_expected_ids = {}
    '''Dictionary containing the expected ids as stored in the root
    widget's `ids`. The root being this widget's root widget from kv.
    '''

    actual_ids = {}
    '''Dictionary containing the actual ids as stored in the root
    widget's `ids`. The root being this widget's root widget from kv.

    The ids is saved here during the `on_kv_post` callback.
    '''

    expected_prop_values = {}
    '''A dict of property names and the values they are expected to have
    during the on_kv_post dispatch.
    '''

    actual_prop_values = {}
    '''A dict of property names and the values they actually had
    during the on_kv_post dispatch.
    '''

    def __init__(self, name='none', **kwargs):
        self.kv_pre_events = self.kv_pre_events[:]
        self.kv_applied_events = self.kv_applied_events[:]
        self.kv_post_events = self.kv_post_events[:]
        self.events_in_pre = self.events_in_pre[:]
        self.events_in_applied = self.events_in_applied[:]
        self.events_in_post = self.events_in_post[:]

        self.name = name

        super(TrackCallbacks, self).__init__(**kwargs)
        self.instantiated_widgets.append(self)

    def add(self, name, event):
        '''Add name to the list of the names added in the callbacks for this
        event.
        '''
        events = getattr(self, 'kv_{}_events'.format(event))
        events.append(name)

    @classmethod
    def check(cls, testcase):
        '''Checks that all the widgets of this class pass all the assertions.
        '''
        for widget in cls.instantiated_widgets:
            # check that all the events match
            for event in ('pre', 'applied', 'post'):
                cls.check_event(widget, event, testcase)

            # check that the ids are properly saved during on_kv_post dispatch
            expected = {
                k: v.__self__ for k, v in widget.my_roots_expected_ids.items()}
            actual = {k: v.__self__ for k, v in widget.actual_ids.items()}
            testcase.assertEqual(expected, actual)

            # check that the root widget is as expected
            testcase.assertIs(
                widget.root_widget and widget.root_widget.__self__,
                widget.actual_root_widget and
                widget.actual_root_widget.__self__,
                'expected "{}", got "{}" instead for root_widget'.format(
                    widget.root_widget and widget.root_widget.name,
                    widget.actual_root_widget and
                    widget.actual_root_widget.name))

            # check that the base widget is as expected
            testcase.assertIs(
                widget.base_widget and widget.base_widget.__self__,
                widget.actual_base_widget and
                widget.actual_base_widget.__self__,
                'expected "{}", got "{}" instead for base_widget'.format(
                    widget.base_widget and widget.base_widget.name,
                    widget.actual_base_widget and
                    widget.actual_base_widget.name))

            # check that the properties have expected values
            testcase.assertEqual(
                widget.expected_prop_values, widget.actual_prop_values)

    @staticmethod
    def check_event(widget, event_name, testcase):
        '''Check that the names are added as expected for this event.
        '''
        events = getattr(widget, 'kv_{}_events'.format(event_name))
        should_be_in = getattr(widget, 'events_in_{}'.format(event_name))

        counter = defaultdict(int)
        for name in events:
            counter[name] += 1

        for name, value in counter.items():
            testcase.assertEqual(
                value, 1,
                '"{}" was present "{}" times for event "{}" for widget "{} '
                '({})"'.format(name, value, event_name, widget.name, widget))

        testcase.assertEqual(
            set(should_be_in), set(events),
            'Expected and actual event callbacks do not match for event "{}" '
            'for widget "{} ({})"'.format(
                event_name, widget.name, widget))

    @staticmethod
    def get_base_class():
        '''The base class to use for widgets during testing so we can use
        this class variables to ease testing.
        '''
        from kivy.uix.widget import Widget

        class TestEventsBase(TrackCallbacks, Widget):

            __events__ = ('on_kv_pre', 'on_kv_applied')

            instantiated_widgets = []

            events_in_pre = [1, ]
            events_in_applied = [1, ]
            events_in_post = [1, ]

            def on_kv_pre(self):
                self.add(1, 'pre')

            def on_kv_applied(self, root_widget):
                self.add(1, 'applied')
                self.actual_root_widget = root_widget

            def on_kv_post(self, base_widget):
                self.add(1, 'post')
                self.actual_base_widget = base_widget
                self.actual_prop_values = {
                    k: getattr(self, k) for k in self.expected_prop_values}

                if self.actual_root_widget is not None:
                    # make a copy of the ids at the current moment
                    self.actual_ids = dict(self.actual_root_widget.ids)

            def apply_class_lang_rules(self, root=None, **kwargs):
                self.dispatch('on_kv_pre')
                super(TestEventsBase, self).apply_class_lang_rules(
                    root=root, **kwargs)
                self.dispatch('on_kv_applied', root)

        return TestEventsBase

    def __repr__(self):
        module = type(self).__module__
        try:
            qualname = type(self).__qualname__
        except AttributeError:  # python 2
            qualname = ''
        return '<Name: "{}" {}.{} object at {}>'.format(
            self.name, module, qualname, hex(id(self)))


class TestKvEvents(unittest.TestCase):

    def test_pure_python_auto_binding(self):
        class TestEventsPureAuto(TrackCallbacks.get_base_class()):
            instantiated_widgets = []

        widget = TestEventsPureAuto()
        widget.root_widget = None
        widget.base_widget = widget
        TestEventsPureAuto.check(self)

    def test_pure_python_callbacks(self):
        class TestEventsPure(TrackCallbacks.get_base_class()):
            instantiated_widgets = []

            events_in_pre = [1, 2]
            events_in_applied = [1, 2]
            events_in_post = [1, 2]

            def __init__(self, **kwargs):
                self.fbind('on_kv_pre', lambda _: self.add(2, 'pre'))
                self.fbind(
                    'on_kv_applied', lambda _, x: self.add(2, 'applied'))
                self.fbind('on_kv_post', lambda _, x: self.add(2, 'post'))

                super(TestEventsPure, self).__init__(**kwargs)

        widget = TestEventsPure()
        widget.root_widget = None
        widget.base_widget = widget

        widget.fbind('on_kv_pre', lambda _: widget.add(3, 'pre'))
        widget.fbind('on_kv_applied', lambda _, x: widget.add(3, 'applied'))
        widget.fbind('on_kv_post', lambda _, x: widget.add(3, 'post'))

        TestEventsPure.check(self)

    def test_instantiate_from_kv(self):
        from kivy.lang import Builder

        class TestEventsFromKV(TrackCallbacks.get_base_class()):
            instantiated_widgets = []

        widget = Builder.load_string('TestEventsFromKV')
        self.assertIsInstance(widget, TestEventsFromKV)
        widget.root_widget = widget
        widget.base_widget = widget

        widget.check(self)

    def test_instantiate_from_kv_with_event(self):
        from kivy.lang import Builder

        class TestEventsFromKVEvent(TrackCallbacks.get_base_class()):
            instantiated_widgets = []

        widget = Builder.load_string(textwrap.dedent("""
        TestEventsFromKVEvent:
            events_in_post: [1, 2]
            on_kv_pre: self.add(2, 'pre')
            on_kv_applied: self.add(2, 'applied')
            on_kv_post: self.add(2, 'post')
            root_widget: self
            base_widget: self
        """))

        self.assertIsInstance(widget, TestEventsFromKVEvent)
        widget.check(self)

    def test_instantiate_from_kv_with_child(self):
        from kivy.lang import Builder

        class TestEventsFromKVChild(TrackCallbacks.get_base_class()):
            instantiated_widgets = []

        widget = Builder.load_string(textwrap.dedent("""
        TestEventsFromKVChild:
            events_in_post: [1, 2]
            on_kv_pre: self.add(2, 'pre')
            on_kv_applied: self.add(2, 'applied')
            on_kv_post: self.add(2, 'post')
            root_widget: self
            base_widget: self
            name: 'root'
            my_roots_expected_ids: {'child_widget': child_widget}
            TestEventsFromKVChild:
                events_in_post: [1, 2]
                on_kv_pre: self.add(2, 'pre')
                on_kv_applied: self.add(2, 'applied')
                on_kv_post: self.add(2, 'post')
                root_widget: root
                base_widget: root
                name: 'child'
                id: child_widget
                my_roots_expected_ids: {'child_widget': self}
        """))

        self.assertIsInstance(widget, TestEventsFromKVChild)
        widget.check(self)

    def test_instantiate_from_kv_with_child_inherit(self):
        from kivy.lang import Builder

        class TestEventsFromKVChildInherit(TrackCallbacks.get_base_class()):
            instantiated_widgets = []

        widget = Builder.load_string(textwrap.dedent("""
        <TestEventsFromKVChildInherit2@TestEventsFromKVChildInherit>:
            on_kv_pre: self.add(3, 'pre')
            on_kv_applied: self.add(3, 'applied')
            on_kv_post: self.add(3, 'post')

        <TestEventsFromKVChildInherit3@TestEventsFromKVChildInherit2>:
            on_kv_pre: self.add(4, 'pre')
            on_kv_applied: self.add(4, 'applied')
            on_kv_post: self.add(4, 'post')
            some_value: 'fruit'
            TestEventsFromKVChildInherit2:
                events_in_applied: [1, 2, 3]
                events_in_post: [1, 2, 3, 4]
                on_kv_pre: self.add(4, 'pre')
                on_kv_applied: self.add(4, 'applied')
                on_kv_post: self.add(4, 'post')
                root_widget: root
                base_widget: self.parent.parent
                name: 'third child'
                id: third_child
                my_roots_expected_ids: {'third_child': self}

        <TestEventsFromKVChildInherit>:
            on_kv_pre: self.add(2, 'pre')
            on_kv_applied: self.add(2, 'applied')
            on_kv_post: self.add(2, 'post')
            another_value: 'apple'

        TestEventsFromKVChildInherit:
            events_in_applied: [1, 2]
            events_in_post: [1, 2, 3]
            on_kv_pre: self.add(3, 'pre')
            on_kv_applied: self.add(3, 'applied')
            on_kv_post: self.add(3, 'post')
            root_widget: self
            base_widget: self
            name: 'root'
            my_roots_expected_ids: \
                {'second_child': second_child, 'first_child': first_child}
            TestEventsFromKVChildInherit:
                events_in_applied: [1, 2]
                events_in_post: [1, 2, 3]
                on_kv_pre: self.add(3, 'pre')
                on_kv_applied: self.add(3, 'applied')
                on_kv_post: self.add(3, 'post')
                root_widget: root
                base_widget: root
                name: 'first child'
                id: first_child
                my_roots_expected_ids: \
                    {'second_child': second_child, 'first_child': self}
            TestEventsFromKVChildInherit3:
                events_in_applied: [1, 2, 3, 4]
                events_in_post: [1, 2, 3, 4, 5]
                on_kv_pre: self.add(5, 'pre')
                on_kv_applied: self.add(5, 'applied')
                on_kv_post: self.add(5, 'post')
                root_widget: root
                base_widget: root
                name: 'second child'
                some_value: first_child.another_value
                expected_prop_values: {'some_value': 'apple'}
                id: second_child
                my_roots_expected_ids: \
                    {'second_child': self, 'first_child': first_child}
        """))

        widget.check(self)
