.. _packaging_ios:

Create a package for iOS
========================

The overall process for creating a package for iOS can be explained in 4 steps:

#. :ref:`Compile the distribution` (python + modules for iOS)
#. :ref:`Create an Xcode project` (and link your source code)
#. :ref:`Update the Xcode project`
#. :ref:`Customize`

Prerequisites
-------------

You need to install some dependencies, like Cython, autotools, etc. We
encourage you to use `Homebrew <https://brew.sh>`_ to install
those dependencies:

.. parsed-literal::

    $ brew install autoconf automake libtool pkg-config
    $ brew link libtool
    $ pip install |cython_install|

For more detail, see :ref:`iOS Prerequisites <packaging_ios_prerequisites>`.
Just ensure that everything is ok before starting the second step!

.. _Compile the distribution:

Compile the distribution
------------------------

Open a terminal, and type::

    $ pip install kivy-ios
    $ toolchain build kivy

If you experience any issues, please refer to our
`user group <https://groups.google.com/forum/#!forum/kivy-users>`_ or the
`kivy-ios project page <https://github.com/kivy/kivy-ios>`_.

.. _Create an Xcode project:

Create an Xcode project
-----------------------

Before proceeding to the next step, ensure your application entry point is a file
named `main.py`.

We provide a script that creates an initial Xcode project to start with. In the
command line below, replace `title` with your project name. It must be a
name without any spaces or illegal characters::

    $ toolchain create <title> <app_directory>
    $ toolchain create Touchtracer ~/code/kivy/examples/demo/touchtracer

.. Note::
    You must use a fully qualified path to your application directory.

A directory named `<title>-ios` will be created, with an Xcode project in it.
You can open the Xcode project::

    $ open touchtracer-ios/touchtracer.xcodeproj

Then click on `Play`, and enjoy.

.. Note::

    Everytime you press `Play`, your application directory will be synced to
    the `<title>-ios/YourApp` directory. Don't make changes in the -ios
    directory directly.

.. _Update the Xcode project:

Update the Xcode project
------------------------

Let's say you want to add numpy to your project but you did not compile it
prior to creating your XCode project. First, ensure it is built::

    $ toolchain build numpy

Then, update your Xcode project::

    $ toolchain update touchtracer-ios

All the libraries / frameworks necessary to run all the compiled recipes will be
added to your Xcode project.

.. _Customize:

Customize the Xcode project
---------------------------

There are various ways to customize and configure your app. Please refer
to the `kivy-ios <https://www.github.com/kivy/kivy-ios>`_ documentation
for more information.

.. _Known issues:

Known issues
------------

All known issues with packaging for iOS are currently tracked on our
`issues <https://github.com/kivy/kivy-ios/issues>`_  page. If you encounter
an issue specific to packaging for iOS that isn't listed there, please feel
free to file a new issue, and we will get back to you on it.

While most are too technical to be written here, one important known issue is
that removing some libraries (e.g. SDL_Mixer for audio) is currently not
possible because the kivy project requires it. We will fix this and others
in future versions.

.. _ios_packaging_faq:

FAQ
---

Application quit abnormally!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In debug mode, all the print statements are sent to the Xcode console.
Looking and grep'ing these logs is highly encouraged. You'll probably find
that you missed to build/install a required dependency. Not your case?
Feel free to ask on our Discord ``support`` channels.

How can Apple accept a python app?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We managed to merge the app binary with all the libraries into a single binary,
called libpython. This means all binary modules are loaded beforehand, so
nothing is dynamically loaded.

Have you already submitted a Kivy application to the App store?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, absolutely. `Kivy Apps in the Apple App Store <https://github.com/kivy/kivy/wiki/List-of-Kivy-Projects#kivy-apps-in-the-apple-app-store>`_.
