.. _basic:

Kivy Basics
===========

Installation of Kivy environment
--------------------------------

Kivy depends on multiples dependencies, such as pygame, gstreamer, PIL,
cairo, and more. All of them are not required, but depending the
platform you're working on, it can be a pain to install them. For
Windows and MacOSX, we provide a portable package that you can just
unzip and use.

.. toctree::
    :maxdepth: 1

    /installation/installation-windows.rst
    /installation/installation-macosx.rst
    /installation/installation-linux.rst

If you want to install everything yourself, ensure that you have at
least `Cython <http://cython.org>`_, `Pygame <http://pygame.org>`. A
typical pip
installation look like::

    pip install cython
    pip install hg+http://bitbucket.org/pygame/pygame
    pip install kivy

The `development version <https://github.com/kivy/kivy>`_ can be
installed with git::

    git clone https://github.com/kivy/kivy
    make

Create an application
---------------------

Creating a kivy application is as simple as:

- subclassing the :class:`~kivy.app.App` class
- implementing its :meth:`~kivy.app.App.build` method so it returns a
  :class:`~kivy.uix.Widget` instance (the root of your widget tree) -
  instantiating this class, and call its :meth:`~kivy.app.App.run`
  method.

Here is an example of such a minimal application::

    from kivy.app import App
    from kivy.uix.label import Label


    class MyApp(App):
        def build(self):
            return Label(text='Hello world')


    if __name__ == '__main__':
        MyApp().run()

You can save this to a text file, `main.py` for example, and run it.

Running the application
-----------------------
To run the application, follow the instructions for your operating system:

    Linux
        Follow the instructions for
        :ref:`running Kivy application on Linux <linux-run-app>`::

            $ python main.py

    Windows
        Follow the instructions for
        :ref:`running Kivy application on Windows <windows-run-app>`::

            $ python main.py
            # or
            C:\appdir>kivy.bat main.py

    Mac OS X
        Follow the instructions for
        :ref:`running Kivy application on MacOSX <macosx-run-app>`::

            $ kivy main.py

    Android
        Your application needs some complementary files to be able to run on
        Android.  See :doc:`android` for further reference.

A window should open, showing a sole button (with the label 'Hello World') that
covers the entire window's area. That's all there is to it.

.. image:: images/quickstart.jpg
    :align: center


Customize the application
-------------------------

Platform specifics
------------------

