import unittest
import textwrap
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty


KV_CODE = '''
<EventCounter>:
    on_kv_pre: self.on_kv_pre_from_c()  # This line won't be excuted
    on_kv_post: self.on_kv_post_from_c()

<TestBoxLayout>:
    Label:
        id: label
        text: textinput.text
    TextInput:
        id: textinput
    Button:
        id: button
        on_press: self.text = 'pressed'

<TestLabel>:
    text: 'A'
    on_kv_post: self.text += 'B'
    Label:
        text: root.assert_the_text_hasnt_changed_yet() or 'hello'
<OtherTestLabel@TestLabel>:
    on_kv_post: self.text += 'C'
    height: self.assert_the_text_hasnt_changed_yet() or 200
    Label:
        text: root.assert_the_text_hasnt_changed_yet() or 'hello2'
'''
KV_FILENAME = 'test_kv_filename'


def setUpModule():
    Builder.load_string(KV_CODE, filename=KV_FILENAME)


def tearDownModule():
    Builder.unload_file(KV_FILENAME)
    u = Factory.unregister
    u('EventCounter')
    u('TestWidget')
    u('TestBoxLayout')
    u('TestLabel')
    u('OtherTestLabel')


class LangTestCase(unittest.TestCase):

    def test_how_may_times_handlers_are_called(self):
        '''NOTE: Event handlers are supposed to be called in the order below:
                 'root rule' -> 'class rule' -> 'default handler'
        '''
        testcase = self
        ae = self.assertEqual
        NP = NumericProperty

        class EventCounter(Factory.Widget):
            does_have_root_rule = BooleanProperty(True)
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

            def on_kv_post(self):
                self._n_post_from_d += 1
                self.assert_all_handlers_were_called_correctly()

            def on_kv_post_from_c(self):
                self._n_post_from_c += 1
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 1 if self.does_have_root_rule else 0)
                ae(self._n_post_from_c, 1)
                ae(self._n_post_from_d, 0)

            def on_kv_post_from_r(self):
                if not self.does_have_root_rule:
                    testcase.fail(
                        "Strange. The handler was called even though "
                        "the widget doesn't have root rule.")
                self._n_post_from_r += 1
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 1)
                ae(self._n_post_from_c, 0)
                ae(self._n_post_from_d, 0)

            def assert_all_handlers_were_called_correctly(self):
                ae(self._n_pre_from_d, 1)
                ae(self._n_post_from_r, 1 if self.does_have_root_rule else 0)
                ae(self._n_post_from_c, 1)
                ae(self._n_post_from_d, 1)

        # case #1: Without root rule
        root = EventCounter(does_have_root_rule=False)
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

        # case #3: If the user add a widget during 'on_kv_pre()' and
        #          '__init__()', is 'on_kv_post' still fired exactly
        #          once on that widget?
        class TestWidget(Factory.Widget):
            def __init__(self, **kwargs):
                super(TestWidget, self).__init__(**kwargs)
                self._ec1 = EventCounter(does_have_root_rule=False)
                self.add_widget(self._ec1)

            def on_kv_pre(self):
                self._ec2 = EventCounter(does_have_root_rule=False)
                self.add_widget(self._ec2)
        root = TestWidget()
        root._ec1.assert_all_handlers_were_called_correctly()
        root._ec2.assert_all_handlers_were_called_correctly()

    def test_rule_is_applied_on_kv_post(self):
        tc = self

        class TestBoxLayout(Factory.BoxLayout):
            def on_kv_post(self):
                # ---------------
                # test children
                # ---------------
                ids = self.ids
                tc.assertIn('textinput', ids)
                tc.assertIn('label', ids)
                tc.assertIn('button', ids)

                # check property binding
                textinput = ids.textinput
                label = ids.label
                label.text = 'A'
                textinput.text = 'B'
                tc.assertEqual(label.text, 'B')

                # check event handler
                button = ids.button
                button.text = ''
                button.dispatch('on_press')
                tc.assertEqual(button.text, 'pressed')

                # ---------------
                # test parent
                # ---------------
                parent = self.parent

                # check 'parent' property
                tc.assertTrue(parent is not None)

                # check property binding
                parent.height = 1
                parent.width = 50
                tc.assertEqual(parent.height, 100)

                # check event handler
                parent.height = 1
                parent.dispatch('on_press')
                tc.assertEqual(parent.height, 123)

        root = Builder.load_string(textwrap.dedent('''
        Widget:
            Button:
                height: self.width * 2
                on_press: self.height = 123
                TestBoxLayout:
        '''))

    def test_property_is_evaluated_before_on_kv_post_is_fired(self):
        ae = self.assertEqual

        class TestLabel(Factory.Label):
            def assert_the_text_hasnt_changed_yet(self):
                ae(self.text, 'A')

        root = Builder.load_string(textwrap.dedent('''
        BoxLayout:
            OtherTestLabel:
                id: label
                on_kv_post: self.text += 'D'
        '''))
        ae(root.ids.label.text, 'ADCB')