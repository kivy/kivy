Threading example with Kivy
------------
An example showing how to use threading and @mainthread decorator.

Python code::

    import threading
    import time

    from kivy.clock import mainthread
    from kivy.lang import Builder
    from kivy.properties import NumericProperty, StringProperty
    from kivy.uix.boxlayout import BoxLayout

    __all__ = ('MyBL',)


    class MyBL(BoxLayout):
        counter = NumericProperty()
        data_label = StringProperty("Nothing yet!")

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            threading.Thread(target=self.get_data).start()

        def get_data(self):
            while App.get_running_app():
                # get data here
                # sock.recv(1024) or how you do it
                time.sleep(1)

                # if you change the UI you need to do it on main thread
                self.set_data_label(self.counter)

                self.counter += 1

        @mainthread
        def set_data_label(self, counter: int):
            self.data_label = str(counter)


    Builder.load_string("""
    <MyBL>:
        Label:
            font_size: "30sp"
            text: "Some Data"

        Label:
            font_size: "30sp"
            text: root.data_label
    """)


    if __name__ == '__main__':
        from kivy.app import App

        class MyApp(App):
            def build(self):
                return MyBL()

        MyApp().run()



Created by `el3 <https://discord.com/channels/423249981340778496/1313153966732873808>`_ - December 2, 2024
