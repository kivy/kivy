from common import GraphicUnitTest


class FileChooserTestCase(GraphicUnitTest):

    def test_filechooserlistview(self):
        from kivy.uix.filechooser import FileChooserListView
        r = self.render
        wid = FileChooserListView(path='/home/tito/Images')
        r(wid, 2)
