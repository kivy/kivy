from kivy.uix.listview import ListView
from kivy.uix.gridlayout import GridLayout


class MainView(GridLayout):
    '''Implementation of a simple list view with 100 items.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(MainView, self).__init__(**kwargs)

        list_view = ListView(item_strings=[str(index) for index in range(100)])

        self.add_widget(list_view)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
