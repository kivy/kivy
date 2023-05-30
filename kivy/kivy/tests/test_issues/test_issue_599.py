import unittest


class Issue599(unittest.TestCase):

    def test_minmax(self):
        from kivy.event import EventDispatcher
        from kivy.properties import BoundedNumericProperty

        class PropertyWidget(EventDispatcher):
            foo = BoundedNumericProperty(1, min=-5, max=5)

        wid = PropertyWidget()

        self.assertEqual(wid.property('foo').get_min(wid), -5)
        wid.property('foo').set_min(wid, 0)
        self.assertEqual(wid.property('foo').get_min(wid), 0)

        self.assertEqual(wid.property('foo').get_max(wid), 5)
        wid.property('foo').set_max(wid, 10)
        self.assertEqual(wid.property('foo').get_max(wid), 10)
