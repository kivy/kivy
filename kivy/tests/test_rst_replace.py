# coding=utf-8
from kivy.tests.common import GraphicUnitTest
from kivy.uix.rst import RstDocument


class TestRstReplace(RstDocument):
    def __init__(self, **kwargs):
        super(TestRstReplace, self).__init__(**kwargs)
        self.text = '''
.. |uni| unicode:: 0xe4
.. |nbsp| unicode:: 0xA0
.. |text| replace:: is
.. |hop| replace:: replaced
.. _hop: https://kivy.org

|uni| |nbsp| |text| |hop|_
'''


class RstSubstitutionTestCase(GraphicUnitTest):
    def test_rst_replace(self):
        rst = TestRstReplace()
        self.render(rst)

        # RstDocument > Scatter > GridLayout > RstParagraph
        pg = rst.children[0].children[0].children[0]
        rendered_text = pg.text[:]

        # [anchor=] and [ref=] might change in the future
        compare_text = (
            u'[color=202020ff][anchor=hop]'
            u'\xe4 \xA0 is '
            u'[ref=None][color=ce5c00ff]replaced[/color][/ref]'
            u'[/color]'
        )
        self.assertEqual(rendered_text, compare_text)


if __name__ == '__main__':
    import unittest
    unittest.main()
