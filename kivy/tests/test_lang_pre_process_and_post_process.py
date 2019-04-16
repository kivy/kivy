import unittest
import textwrap
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty


class LangTestCase(unittest.TestCase):

    def test_how_many_times_handlers_are_called(self):
        '''NOTE: Event handlers are supposed to be called in the order below:
                 'root rule' -> 'class rule' -> 'default handler'
        '''
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
                assertTrue(parent is not None)

                # check property binding
                parent.x = 0
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
                assertTrue(parent is not None)

                # check property binding
                parent.height = 1
                parent.width = 50
                assertEqual(parent.height, 100)

                # check event handler
                parent.height = 1
                parent.dispatch('on_press')
                assertEqual(parent.height, 123)

            def on_kv_post(self, root_widget):
                self._the_handler_was_actually_called = True
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
                              '_the_handler_was_actually_called'))
