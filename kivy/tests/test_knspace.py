
import unittest


class KNSpaceTestCase(unittest.TestCase):

    def test_not_exists(self):
        from kivy.uix.behaviors.knspace import knspace
        self.assertRaises(AttributeError, lambda: knspace.label)
        knspace.property('label')
        self.assertIsNone(knspace.label)

    def test_simple(self):
        from kivy.lang import Builder
        from kivy.uix.behaviors.knspace import knspace

        w = Builder.load_string('''
<NamedLabel@KNSpaceBehavior+Label>

NamedLabel:
    name: 'label'
    text: 'Hello'
''')
        self.assertEqual(knspace.label, w)
        self.assertIs(w, knspace.label.__self__)
        self.assertIsNot(w, knspace.label)
        self.assertEqual('Hello', knspace.label.text)
        w.text = 'Goodbye'
        self.assertEqual('Goodbye', knspace.label.text)

    def test_simple2(self):
        from kivy.lang import Builder
        from kivy.uix.behaviors.knspace import knspace

        w = Builder.load_string('''
<NamedLabel@KNSpaceBehavior+Label>

BoxLayout:
    NamedLabel:
        name: 'label1'
        text: 'Hello'
    NamedLabel:
        name: 'label2'
        text: 'Goodbye'
''')
        self.assertEqual('Hello', knspace.label1.text)
        self.assertEqual('Goodbye', knspace.label2.text)

    def test_simple_binding(self):
        from kivy.lang import Builder
        from kivy.uix.behaviors.knspace import knspace

        w = Builder.load_string('''
#:import knspace kivy.uix.behaviors.knspace.knspace
<NamedLabel@KNSpaceBehavior+Label>

BoxLayout:
    text: knspace.label.text if knspace.label else ''
    NamedLabel:
        name: 'label'
        text: 'Hello'
''')
        self.assertEqual('Hello', w.text)
        knspace.label.text = 'Goodbye'
        self.assertEqual('Goodbye', w.text)

    def test_simple_name_change(self):
        from kivy.lang import Builder
        from kivy.uix.behaviors.knspace import knspace

        w = Builder.load_string('''
<NamedLabel@KNSpaceBehavior+Label>

NamedLabel:
    name: 'label'
    text: 'Hello'
''')
        self.assertEqual(w, knspace.label)
        w.name = 'named_label'
        self.assertIsNone(knspace.label)
        self.assertEqual(w, knspace.named_label)

    def test_fork(self):
        from kivy.lang import Builder
        from kivy.uix.behaviors.knspace import knspace

        w = Builder.load_string('''
<NamedLabel@KNSpaceBehavior+Label>

BoxLayout:
    NamedLabel:
        knspace: 'fork'
        name: 'label'
        text: 'Hello'
    NamedLabel:
        knspace: 'fork'
        name: 'label'
        text: 'Goodbye'
''')
        self.assertRaises(AttributeError, lambda: knspace.label)
        self.assertEqual(w.children[0].knspace.label.text, 'Goodbye')
        self.assertEqual(w.children[1].knspace.label.text, 'Hello')
