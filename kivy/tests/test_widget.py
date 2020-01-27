import unittest
from tempfile import mkdtemp
from shutil import rmtree


class WidgetTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.uix.widget import Widget
        self.cls = Widget
        self.root = Widget()

    def test_add_remove_widget(self):
        root = self.root
        self.assertEqual(root.children, [])
        c1 = self.cls()
        root.add_widget(c1)
        self.assertEqual(root.children, [c1])
        root.remove_widget(c1)
        self.assertEqual(root.children, [])

    def test_invalid_add_widget(self):
        from kivy.uix.widget import WidgetException
        try:
            # None of them should work
            self.root.add_widget(None)
            self.root.add_widget(WidgetException)
            self.root.add_widget(self.cls)
            self.fail()
        except WidgetException:
            pass

    def test_position(self):
        wid = self.root
        wid.x = 50
        self.assertEqual(wid.x, 50)
        self.assertEqual(wid.pos, [50, 0])
        wid.y = 60
        self.assertEqual(wid.y, 60)
        self.assertEqual(wid.pos, [50, 60])
        wid.pos = (0, 0)
        self.assertEqual(wid.pos, [0, 0])
        self.assertEqual(wid.x, 0)
        self.assertEqual(wid.y, 0)

    def test_size(self):
        wid = self.root
        wid.width = 50
        self.assertEqual(wid.width, 50)
        self.assertEqual(wid.size, [50, 100])
        wid.height = 60
        self.assertEqual(wid.height, 60)
        self.assertEqual(wid.size, [50, 60])
        wid.size = (100, 100)
        self.assertEqual(wid.size, [100, 100])
        self.assertEqual(wid.width, 100)
        self.assertEqual(wid.height, 100)

    def test_collision(self):
        wid = self.root
        self.assertEqual(wid.pos, [0, 0])
        self.assertEqual(wid.size, [100, 100])
        self.assertEqual(wid.collide_point(-1, -1), False)
        self.assertEqual(wid.collide_point(0, 0), True)
        self.assertEqual(wid.collide_point(50, 50), True)
        self.assertEqual(wid.collide_point(100, 100), True)
        self.assertEqual(wid.collide_point(200, 0), False)
        self.assertEqual(wid.collide_point(500, 500), False)

    # Currently rejected with a Shader didn't link, but work alone.
    @unittest.skip("Doesn't work with testsuite, but work alone")
    def test_export_to_png(self):
        from kivy.core.image import Image as CoreImage
        from kivy.uix.button import Button
        from os.path import join

        wid = Button(text='test', size=(200, 100), size_hint=(None, None))
        self.root.add_widget(wid)

        tmp = mkdtemp()
        wid.export_to_png(join(tmp, 'a.png'))
        wid.export_to_png(join(tmp, 'b.png'), scale=.5)
        wid.export_to_png(join(tmp, 'c.png'), scale=2)

        CoreImage(join(tmp, 'a.png')).size == (200, 100)
        CoreImage(join(tmp, 'b.png')).size == (100, 50)
        CoreImage(join(tmp, 'c.png')).size == (400, 200)
        rmtree(tmp)

        self.root.remove_widget(wid)
