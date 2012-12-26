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

Explanation of what's going on in the code above
------------------------------------------------

First off, Let us get familiar with the Kivy app life cycle

.. image:: ../images/Kivy_App_Life_Cycle.svg

As you can see above for all intents and purposes our entry point in to our App
is from run() in our case that is MyApp().run(). We will get back to this; first
let's start from the first line::

    from kivy.app import App

It's required that the base Class of your App inherit from App class. It's 
present in the kivy_installation_dir/kivy/app.py.

.. Note::
    Go ahead and Open up that file if you want to delve deeper into what Kivy
    App class does. We encourage you to open the code and read through as kivy
    is based on Python and uses Sphinx for documentation, documentation for each
    class is in-file.

Similarly on line 2::

    from kivy.uix.label import Label

One important thing to note here is the way packages/classes are laid out in
kivy, `kivy.uix`; is the section that holds its User Interface elements like 
layouts and  widgets.

Moving on to line 5::

    class MyApp(App):

This is where we are `defining` the Base Class of our Kivy App. You should only
ever need to change the name of your app `MyApp` in this line.

Further on to line 7::

    def build(self):

As highlighted by the image above show casing `Kivy App Life Cycle` This is the
function where you should initialize and return your `Root Widget`,This is what
we do on line 8.::

    return Label(text='Hello world')

Here we initialize a Label with text 'Hello World' and return it's instance.
This Label will be the Root Widget of this App.

.. Note::
    Python uses indentation to denote code blocks, there for make note that in
    the code provided at line 9 the class and function definition ends

Now on to the portion that will make our app run at line 11 and 12::

    if __name__ == '__main__':
        MyApp().run()

Here the class `MyApp` is initialized and it's run() method called this
initializes and starts our Kivy application.


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
        Android.  See :doc:`/guide/android` for further reference.

A window should open, showing a sole button (with the label 'Hello World') that
covers the entire window's area. That's all there is to it.

.. image:: ../guide/images/quickstart.jpg
    :align: center


Open a Terminal and set kivy environment variables (look at Platform Specifics
Section) and run the following commands::

    python main.py



Customize the application
-------------------------

Platform specifics
------------------

Opening a Terminal application and set kivy Environment Variables.

    On Windows just double click the kivy.bat and a terminal will be opened with
    all the required variables already set

    On nix* systems open a terminal of your choice and if
    kivy isn't installed globally::

        export python=$PYTHONPATH:/path/to/kivy_installation
