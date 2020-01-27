# coding=utf-8
import unittest
from kivy.tests.common import GraphicUnitTest


def _build_rst():
    from kivy.uix.rst import RstDocument

    class _TestRstReplace(RstDocument):
        def __init__(self, **kwargs):
            super(_TestRstReplace, self).__init__(**kwargs)
            self.text = '''
    .. |uni| unicode:: 0xe4
    .. |nbsp| unicode:: 0xA0
    .. |text| replace:: is
    .. |hop| replace:: replaced
    .. _hop: https://kivy.org

    |uni| |nbsp| |text| |hop|_
    '''

    return _TestRstReplace()


class RstSubstitutionTestCase(GraphicUnitTest):
    # XXX Mathieu - i tried to fix the window context to prevent segfault here
    # but nothing actually works. Works alone, but not after a window restart.
    # On linux:
    #    # 1  0x00007ffff12807e9 in  () at /usr/lib/libnvidia-glcore.so.418.43
    #    # 2  0x00007ffff1288554 in  () at /usr/lib/libnvidia-glcore.so.418.43
    #    # 3  0x00007ffff0e2e3db in  () at /usr/lib/libnvidia-glcore.so.418.43
    #    # 4  0x00007ffff5d5ae15 in __pyx_f_4kivy_8graphics_3vbo_11VertexBatch_draw  # noqa
    #         (__pyx_v_self=0x7fffed641390) at kivy/graphics/vbo.c:6529
    # On OSX:
    #  * thread #1, queue = 'com.apple.main-thread',
    #     stop reason = EXC_BAD_ACCESS (code=1, address=0x0)
    #  * frame #0: 0x00007fff555d9d42 GLEngine`gleRunVertexSubmitImmediate + 1234  # noqa
    #    frame #1: 0x00007fff554c1544 GLEngine`glDrawElements_Exec + 563
    #    frame #2: 0x000000010429d273 vbo.cpython-36m-darwin.so
    #    `__pyx_f_4kivy_8graphics_3vbo_11VertexBatch_draw(
    #    __pyx_v_self=0x000000010cf344f8) at vbo.c:6575 [opt]
    @unittest.skip("Currently segfault, but no idea why.")
    def test_rst_replace(self):
        rst = _build_rst()
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
