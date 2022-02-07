from kivy.app import App
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout


class DropFile(Button):
    def __init__(self, **kwargs):
        super(DropFile, self).__init__(**kwargs)

        # get app instance to add function from widget
        app = App.get_running_app()

        # add function to the list
        app.drops.append(self.on_drop_file)

    def on_drop_file(self, widget, filename):
        # a function catching a dropped file
        # if it's dropped in the widget's area
        if self.collide_point(*Window.mouse_pos):
            # on_drop_file's filename is bytes (py3)
            self.text = filename.decode('utf-8')


class DropApp(App):
    def build(self):
        # set an empty list that will be later populated
        # with functions from widgets themselves
        self.drops = []

        # bind handling function to 'on_drop_file'
        Window.bind(on_drop_file=self.handledrops)

        box = BoxLayout()
        dropleft = DropFile(text='left')
        box.add_widget(dropleft)
        dropright = DropFile(text='right')
        box.add_widget(dropright)
        return box

    def handledrops(self, *args):
        # this will execute each function from list with arguments from
        # Window.on_drop_file
        #
        # make sure `Window.on_drop_file` works on your system first,
        # otherwise the example won't work at all
        for func in self.drops:
            func(*args)


DropApp().run()
