.. _quickstart:

Quickstart
==========

This page will give you a good introduction in Kivy. This assumes you already
have Kivy installed. If you do not, head over to the :ref:`installation`
section.


Create an application
---------------------

The base code for creating an application look something like that :

.. sourcecode:: python

    from kivy.app import App
    from kivy.uix.button import Button

    class MyApp(App):
        def build(self):
            return Button(label='hello world')

    if __name__ == '__main__':
        MyApp().run()

Save it as `myapp.py` and run it with your Python interpreter ::

    $ python myapp.py

You should see a black window open. That's all.

So what did that code do ?

 1. First, we imported :class:`~kivy.app.App` class, to be able to extend it.
 2. Next, we imported :class:`~kivy.uix.button.Button` class, to be able to
    create an instance of a button with a custom label.
 2. Then, we have created our application, based from the App class. We have
    extend the :meth:`~kivy.app.App.build` function to be able to return an
    instance of :class:`~kivy.uix.button.Button`. This instance will be used
    as the root of the widget tree.
 3. Finally, we use :meth:`~kivy.app.App.run` on our application instance to launch the kivy
    process with our application inside.

