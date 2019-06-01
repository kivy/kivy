from kivy.uix.widget import Widget


class MyWidget(Widget):

    def __init__(self, **kwargs):
        super(MyWidget, self).__init__(**kwargs)

        def callback(*l):
            self.x = self.y
        self.fbind('y', callback)
        callback()
