Customized widgets
------------
Example on how to write your own widgets (helps keeping your project fresh and easy to maintain).

Is usually the best option for having better control of your code and separate short tasks with longer tasks. You don't want to bloat your KV-lang scripts with several lines that are pure Python.

Python code::

    # Filepath: libs/customwidget.py
    from kivy.lang import Builder
    from kivy.properties import ColorProperty
    from kivy.uix.behaviors import ButtonBehavior
    from kivy.uix.widget import Widget

    __all__ = ('CustomWidget',)

    Builder.load_string('''
    <CustomWidget>:
        on_release: print("Short code goes here")  # Remove this line if you are using the call from the Python script itself
        canvas.before:
            Color:
                rgba: self.color
            Rectangle:
                size: self.size
                pos: self.pos
    ''')


    class CustomWidget(ButtonBehavior, Widget):
        color = ColorProperty((.5, .5, .5, .8))

        def on_release(self):
            print("Long code goes here")  # remove this definition if you are instead using on_release from your KV code

Once you have created and edited this example code, you are ready to use it in action.
If you want to use this widget with your Python script you simply import it like this: ``from libs.customwidget import CustomWidget``.
If your intentions are to use it within the KV-lang itself, you simply import it like this: ``#:import CustomWidget libs.customwidget.CustomWidget``.

After this example code is imported, you can inherit the widget from any place you want if you use the `Factory <https://kivy.org/doc/stable/api-kivy.factory.html>`_ module.


Created by `kuzeyron <https://discord.com/channels/423249981340778496/1311789935577010188>`_ - November 29, 2024
