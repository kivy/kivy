from kivy.uix.modalview import ModalView
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

# Note the special nature of indentation in the adapter declaration, where
# the adapter: is on one line, then the value side must be given at one level
# of indentation.

Builder.load_string("""
#:import label kivy.uix.label
#:import sla kivy.adapters.simplelistadapter

<ListViewModal>:
    size_hint: None,None
    size: 400,400
    ListView:
        size_hint: .8,.8
        adapter:
            sla.SimpleListAdapter(
            data=["Item #{0}".format(i) for i in range(100)],
            cls=label.Label)
""")


class ListViewModal(ModalView):
    def __init__(self, **kwargs):
        super(ListViewModal, self).__init__(**kwargs)


class MainView(GridLayout):
    """
    Implementation of a ListView using the kv language.
    """

    def __init__(self, **kwargs):
        kwargs['cols'] = 1
        super(MainView, self).__init__(**kwargs)

        listview_modal = ListViewModal()

        self.add_widget(listview_modal)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
