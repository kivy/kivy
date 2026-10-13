Custom plugins
------------
A  way of writing plugins for your project or your intention is to reuse your code within your project.

Python code::

    # Filepath: libs/customevent.py
    from kivy.event import EventDispatcher
    from kivy.properties import ColorProperty

    __all__ = ('CustomEvent',)


    class CustomEvent(EventDispatcher):
        color = ColorProperty((.5, .5, .5, .8))

        def is_going_to_happen(self):
            print("Kivy rules!")

How you import it with your Python script: ``from libs.customevent import CustomEvent``.
With this example you are able to use it with other layouts and widgets by subclassing them like this: ``class OtherLayout(BoxLayout, CustomEvent):``.
Why do we even need the EventDispatcher? There are times when you can't subclass regular classes like ``class MyClass:`` with layouts and widgets.


Created by `kuzeyron <https://discord.com/channels/423249981340778496/1312108446086201384>`_ - November 29, 2024
