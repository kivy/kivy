from kivy.uix.modalview import ModalView
from kivy.uix.listview import ListView
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

Builder.load_string("""
<ListViewModal>:
    size_hint: None,None
    size: 400,400
    ListView:
        size_hint: .8,.8
        item_strings: [str(index) for index in xrange(100)]
""")


class ListViewModal(ModalView):
    def __init__(self, **kwargs):
        super(ListViewModal, self).__init__(**kwargs)


class MainView(GridLayout):
    """Implementation of a list view declared in a kv template.
    """

    def __init__(self, **kwargs):
        kwargs['cols'] = 1
        super(MainView, self).__init__(**kwargs)

        listview_modal = ListViewModal()

        self.add_widget(listview_modal)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
