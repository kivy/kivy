.. _quickstart:

Quickstart
==========

This page explains how to create a simple Kivy *"Hello world"* program.
This assumes you already have Kivy installed. If you do not, head over to the
:ref:`installation` section. We also assume basic `Python <http://docs.python.org/tutorial/>`_
2.x knowledge.


Create an application
---------------------

The base code for creating an application looks like this:

.. sourcecode:: python

    from kivy.app import App
    from kivy.uix.button import Button

    class MyApp(App):
        def build(self):
            return Button(label='Hello World')

    if __name__ == '__main__':
        MyApp().run()

Save it as `myapp.py` and run it with your Python interpreter ::

    $ python myapp.py

You should see a black window open. That's all.

So what did that code do ?

 1. First, we import the :class:`~kivy.app.App` class, to be able to extend it.
    By extending this class, your own class gains several features that
    we already developed for you to make sure it will be recognized by
    Kivy.
 2. Next, we import the :class:`~kivy.uix.button.Button` class, to be able to
    create an instance of a button with a custom label.
 2. Then, we create our application, based on the App class.
    We extend the :meth:`~kivy.app.App.build` function to be able to return an
    instance of :class:`~kivy.uix.button.Button`. This instance will be used
    as the root of the widget tree.
 3. Finally, we call :meth:`~kivy.app.App.run` on our application instance to
    launch the Kivy process with our application inside.

