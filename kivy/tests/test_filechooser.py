from kivy.tests.common import GraphicUnitTest


class FileChooserTestCase(GraphicUnitTest):

    def test_filechooserlistview(self):
        from kivy.uix.filechooser import FileChooserListView
        from os.path import expanduser
        r = self.render
        wid = FileChooserListView(path=expanduser('~'))
        r(wid, 2)
