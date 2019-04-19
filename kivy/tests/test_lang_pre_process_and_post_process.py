import unittest
import textwrap
from collections import defaultdict


class LangTestCase(object):

    def test_how_many_times_handlers_are_called(self):
        '''NOTE: Event handlers are supposed to be called in the order below:
                 'root rule' -> 'class rule' -> 'default handler'
        '''
        from kivy.lang import Builder
        from kivy.factory import Factory
        from kivy.properties import NumericProperty, BooleanProperty
        testcase = self
        ae = self.assertEqual
        NP = NumericProperty

        class EventCounter(Factory.Widget):
            there_is_a_rootrule = BooleanProperty(True)
            _n_pre_from_d = NP(0)  # 'd' stands for 'default handler'
            _n_post_from_r = NP(0)  # 'r' stands for 'root rule'
            _n_post_from_c = NP(0)  # 'c' stands for 'class rule'
            _n_post_from_d = NP(0)

            def on_kv_pre(self):
                self._n_pre_from_d += 1
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 0)
                ae(self._n_post_from_c, 0)
                ae(self._n_post_from_d, 0)

            def on_kv_pre_from_c(self):
                testcase.fail('This method is not supposed to be called')

            def on_kv_pre_from_r(self):
                testcase.fail('This method is not supposed to be called')

            def on_kv_post(self, root_widget):
                self._n_post_from_d += 1
                self.assert_all_handlers_were_called_correctly()

            def on_kv_post_from_c(self):
                self._n_post_from_c += 1
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 1 if self.there_is_a_rootrule else 0)
                ae(self._n_post_from_c, 1)
                ae(self._n_post_from_d, 0)

            def on_kv_post_from_r(self):
                if not self.there_is_a_rootrule:
                    testcase.fail(
                        "Strange. The handler was called even though "
                        "there is no root rule.")
                self._n_post_from_r += 1
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 1)
                ae(self._n_post_from_c, 0)
                ae(self._n_post_from_d, 0)

            def assert_all_handlers_were_called_correctly(self):
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 1 if self.there_is_a_rootrule else 0)
                ae(self._n_post_from_c, 1)
                ae(self._n_post_from_d, 1)

        Builder.load_string(textwrap.dedent('''
        <EventCounter>:
            on_kv_pre: self.on_kv_pre_from_c()  # This line won't be excuted
            on_kv_post: self.on_kv_post_from_c()
        '''))

        # case #1: Without root rule
        root = EventCounter(there_is_a_rootrule=False)
        root.assert_all_handlers_were_called_correctly()

        # case #2: With root rule
        root = Builder.load_string(textwrap.dedent('''
        EventCounter:
            on_kv_pre: self.on_kv_pre_from_r()  # won't be excuted
            on_kv_post: self.on_kv_post_from_r()
            EventCounter:
                id: child
                on_kv_pre: self.on_kv_pre_from_r()  # won't be excuted
                on_kv_post: self.on_kv_post_from_r()
        '''))
        root.assert_all_handlers_were_called_correctly()
        root.ids.child.assert_all_handlers_were_called_correctly()

        # case #3: If the user add a widget during 'on_kv_pre()' or
        #          '__init__()', is 'on_kv_post' still fired exactly
        #          once on that widget?
        class TestWidget(Factory.Widget):
            def __init__(self, **kwargs):
                super(TestWidget, self).__init__(**kwargs)
                self._ec1 = EventCounter(there_is_a_rootrule=False)
                self.add_widget(self._ec1)

            def on_kv_pre(self):
                self._ec2 = EventCounter(there_is_a_rootrule=False)
                self.add_widget(self._ec2)
        root = TestWidget()
        root._ec1.assert_all_handlers_were_called_correctly()
        root._ec2.assert_all_handlers_were_called_correctly()

    def test_each_rule_is_applied_at_proper_timing(self):
        from kivy.lang import Builder
        from kivy.factory import Factory
        tc = self

        class TestBoxLayout(Factory.BoxLayout):
            def assert_my_own_rule_is_applied(self):
                ids = self.ids
                tc.assertIn('textinput', ids)
                tc.assertIn('label', ids)
                tc.assertIn('button', ids)

                # check property binding
                textinput = ids.textinput
                label = ids.label
                label.text = 'A'
                textinput.text = ''
                textinput.text = 'B'
                tc.assertEqual(label.text, 'B')

                # check event handler
                button = ids.button
                button.text = ''
                button.dispatch('on_press')
                tc.assertEqual(button.text, 'pressed')

            def assert_the_rule_i_participate_in_is_applied(
                    self, reverse=False):
                parent = self.parent
                assertTrue = tc.assertFalse if reverse else tc.assertTrue
                assertEqual = tc.assertNotEqual if reverse else tc.assertEqual

                # check 'parent' property
                tc.assertTrue(parent is not None)

                # check property binding
                parent.x = 0
                parent.y = 0
                parent.y = 50
                assertEqual(parent.x, 150)

                # check event handler
                parent.x = 0
                parent.dispatch('on_press')
                assertEqual(parent.x, 200)

            def assert_the_rule_i_dont_participate_in_is_applied(
                    self, reverse=False):
                parent = self.parent
                assertTrue = tc.assertFalse if reverse else tc.assertTrue
                assertEqual = tc.assertNotEqual if reverse else tc.assertEqual

                # check 'parent' property
                tc.assertTrue(parent is not None)

                # check property binding
                parent.height = 1
                parent.width = 0
                parent.width = 50
                assertEqual(parent.height, 100)

                # check event handler
                parent.height = 1
                parent.dispatch('on_press')
                assertEqual(parent.height, 123)

            def on_kv_applied(self):
                self._on_kv_applied_was_actually_fired = True
                self.assert_my_own_rule_is_applied()
                self.assert_the_rule_i_participate_in_is_applied(reverse=True)
                self.assert_the_rule_i_dont_participate_in_is_applied(
                    reverse=True)

            def on_kv_post(self, root_widget):
                self._on_kv_post_was_actually_fired = True
                self.assert_my_own_rule_is_applied()
                self.assert_the_rule_i_participate_in_is_applied()
                self.assert_the_rule_i_dont_participate_in_is_applied()
        root = Builder.load_string(textwrap.dedent('''
        <TestBoxLayout>:
            Label:
                id: label
                text: textinput.text
            TextInput:
                id: textinput
            Button:
                id: button
                on_press: self.text = 'pressed'
        <TestButton@Button>:
            x: self.y + 100
            on_press: self.x = 200
            TestBoxLayout:
        TestButton:
            height: self.width * 2
            on_press: self.height = 123
        '''))
        tc.assertTrue(hasattr(root.children[0],
                              '_on_kv_applied_was_actually_fired'))
        tc.assertTrue(hasattr(root.children[0],
                              '_on_kv_post_was_actually_fired'))


class TrackCallbacks(object):

    kv_pre_events = []

    kv_applied_events = []

    kv_post_events = []

    events_in_pre = []

    events_in_applied = []

    events_in_post = []

    instantiated_widgets = []

    root_widget = None

    base_widget = None

    actual_root_widget = None

    actual_base_widget = None

    name = 'none'

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
        events = getattr(self, 'kv_{}_events'.format(event))
        events.append(name)

    @classmethod
    def check(cls, testcase):
        for widget in cls.instantiated_widgets:
            for event in ('pre', 'applied', 'post'):
                cls.check_event(widget, event, testcase)

            testcase.assertIs(
                widget.root_widget and widget.root_widget.__self__,
                widget.actual_root_widget and
                widget.actual_root_widget.__self__,
                'expected "{}", got "{}" instead for root_widget'.format(
                    widget.root_widget and widget.root_widget.name,
                    widget.actual_root_widget and
                    widget.actual_root_widget.name))
            testcase.assertIs(
                widget.base_widget and widget.base_widget.__self__,
                widget.actual_base_widget and
                widget.actual_base_widget.__self__,
                'expected "{}", got "{}" instead for base_widget'.format(
                    widget.base_widget and widget.base_widget.name,
                    widget.actual_base_widget and
                    widget.actual_base_widget.name))

    @staticmethod
    def check_event(widget, event_name, testcase):
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

            def apply_class_lang_rules(self, root=None, **kwargs):
                self.dispatch('on_kv_pre')
                super(TestEventsBase, self).apply_class_lang_rules(
                    root=root, **kwargs)
                self.dispatch('on_kv_applied', root)

        return TestEventsBase

    def __repr__(self):
        module = type(self).__module__
        qualname = type(self).__qualname__
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
            TestEventsFromKVChild:
                events_in_post: [1, 2]
                on_kv_pre: self.add(2, 'pre')
                on_kv_applied: self.add(2, 'applied')
                on_kv_post: self.add(2, 'post')
                root_widget: root
                base_widget: root
                name: 'child'
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
            TestEventsFromKVChildInherit2:
                events_in_applied: [1, 2, 3]
                events_in_post: [1, 2, 3, 4]
                on_kv_pre: self.add(4, 'pre')
                on_kv_applied: self.add(4, 'applied')
                on_kv_post: self.add(4, 'post')
                root_widget: root
                base_widget: self.parent.parent
                name: 'third child'

        <TestEventsFromKVChildInherit>:
            on_kv_pre: self.add(2, 'pre')
            on_kv_applied: self.add(2, 'applied')
            on_kv_post: self.add(2, 'post')

        TestEventsFromKVChildInherit:
            events_in_applied: [1, 2]
            events_in_post: [1, 2, 3]
            on_kv_pre: self.add(3, 'pre')
            on_kv_applied: self.add(3, 'applied')
            on_kv_post: self.add(3, 'post')
            root_widget: self
            base_widget: self
            name: 'root'
            TestEventsFromKVChildInherit:
                events_in_applied: [1, 2]
                events_in_post: [1, 2, 3]
                on_kv_pre: self.add(3, 'pre')
                on_kv_applied: self.add(3, 'applied')
                on_kv_post: self.add(3, 'post')
                root_widget: root
                base_widget: root
                name: 'first child'
            TestEventsFromKVChildInherit3:
                events_in_applied: [1, 2, 3, 4]
                events_in_post: [1, 2, 3, 4, 5]
                on_kv_pre: self.add(5, 'pre')
                on_kv_applied: self.add(5, 'applied')
                on_kv_post: self.add(5, 'post')
                root_widget: root
                base_widget: root
                name: 'second child'
        """))

        widget.check(self)
