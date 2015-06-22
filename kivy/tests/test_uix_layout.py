'''
uix.layout tests
================
Layout class is Abstract Base Class.
'''

import unittest

from kivy.uix.layout import Layout


class UixLayoutTest(unittest.TestCase):

    def test_instantiation(self):
        with self.assertRaises(Exception):
            layout = Layout()
