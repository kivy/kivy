'''
Accordion unit tests
====================
'''

import unittest


class AccordionItemTitleTestCase(unittest.TestCase):
    '''Tests for the new :attr:`AccordionItem.title_class` API
    (added in 3.0.0 to replace the removed deprecated KV templates
    ``title_template`` / ``title_args``).
    '''

    def test_default_title_class(self):
        from kivy.uix.accordion import AccordionItem, AccordionItemTitle
        item = AccordionItem()
        self.assertIs(item.title_class, AccordionItemTitle)

    def test_string_title_class_resolved_via_factory(self):
        from kivy.uix.accordion import AccordionItem, AccordionItemTitle
        item = AccordionItem(title='hello')
        item.title_class = 'AccordionItemTitle'
        self.assertIs(item.title_class, AccordionItemTitle)

    def test_custom_python_title_class(self):
        from kivy.uix.accordion import AccordionItem, AccordionItemTitle

        class MyTitle(AccordionItemTitle):
            pass

        item = AccordionItem(title='hi', title_class=MyTitle)
        self.assertIs(item.title_class, MyTitle)

    def test_accordion_basic_construction(self):
        # Smoke test: building an Accordion with AccordionItems still works
        # end-to-end after the templates removal.
        from kivy.uix.accordion import Accordion, AccordionItem
        from kivy.uix.label import Label

        acc = Accordion()
        for x in range(3):
            it = AccordionItem(title='Title %d' % x)
            it.add_widget(Label(text='content %d' % x))
            acc.add_widget(it)
        self.assertEqual(len(acc.children), 3)
        for it in acc.children:
            self.assertIsInstance(it, AccordionItem)

    def test_title_template_removed(self):
        # title_template was removed; instantiating with it should raise.
        from kivy.uix.accordion import AccordionItem
        with self.assertRaises(Exception):
            AccordionItem(title_template='AccordionItemTitle')


if __name__ == '__main__':
    unittest.main()
