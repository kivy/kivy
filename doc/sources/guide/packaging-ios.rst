.. _packaging_ios:

Create a package for IOS
========================

.. note::

    Currently, packages for iOS can only be generated with Python 2.7. Python
    3.3+ support is on the way.

The overall process for creating a package for IOS can be explained in 4 steps:

#. Compile python + modules for IOS
#. Create an Xcode project and link your source code
#. Customize

Prerequisites
-------------

You need to install some dependencies, like cython, autotools, etc. We
encourage you to use `Homebrew <http://mxcl.github.com/homebrew/>`_ to install
those dependencies::

    brew install autoconf automake libtool pkg-config
    brew link libtool
    sudo easy_install pip
    sudo pip install cython==0.23

For more detail, see :ref:`IOS Prerequisites <packaging_ios_prerequisites>`.
Just ensure that everything is ok before starting the second step!

.. _Compile the distribution:

Compile the distribution
------------------------

Open a terminal, and type::

    $ git clone git://github.com/kivy/kivy-ios
    $ cd kivy-ios
    $ ./toolchain.py build kivy

Most of the python distribution is packed into `python27.zip`. If you
experience any issues, please refer to our
`user group <https://groups.google.com/forum/#!forum/kivy-users>`_ or the
`kivy-ios project page <https://github.com/kivy/kivy-ios>`_.

.. _Create an Xcode project:

Create an Xcode project
-----------------------

Before proceeding to the next step, ensure your application entry point is a file
named `main.py`.

We provide a script that creates an initial Xcode project to start with. In the
command line below, replace `test` with your project name. It must be a
name without any spaces or illegal characters::

    $ ./toolchain.py create <title> <app_directory>
    $ ./toolchain.py create Touchtracer ~/code/kivy/examples/demo/touchtracer

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

Updating an Xcode project
-------------------------

Let's say you want to add numpy to your project but you did not compile it
prior to creating your XCode project. First, ensure it is built::

    $ ./toolchain.py build numpy

Then, update your Xcode project::

    $ ./toolchain.py update touchtracer-ios

All the libraries / frameworks necessary to run all the compiled recipes will be
added to your Xcode project.

.. _Customize:

Customize
---------

There are various ways to customize and configure your app. Please refer
to the `kivy-ios <http://www.github.com/kivy/kivy-ios>`_ documentation
for more information.

.. _Known issues:

Known issues
------------

All known issues with packaging for iOS are currently tracked on our `issues <https://github.com/kivy/kivy-ios/issues>`_ page. If you encounter an issue specific to packaging for iOS that isn't listed there, please feel free to file a new issue, and we will get back to you on it.

While most are too technical to be written here, one important known issue is that some libraries (like SDL_Mixer for audio) is currently not possible because the kivy project requires it. We will fix this and others in future versions.

.. _ios_packaging_faq:

FAQ
---

Application quit abnormally!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all the print statements to the console and files are ignored. If
you have an issue when running your application, you can activate the log by
commenting out this line in `main.m`::

    putenv("KIVY_NO_CONSOLELOG=1");

Then you should see all the Kivy logging on the Xcode console.

How can Apple accept a python app ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We managed to merge the app binary with all the libraries into a single binary,
called libpython. This means all binary modules are loaded beforehand, so
nothing is dynamically loaded.

Have you already submited a Kivy application to the App store ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, check:

- `Defletouch on iTunes <http://itunes.apple.com/us/app/deflectouch/id505729681>`_,
- `ProcessCraft on iTunes <http://itunes.apple.com/us/app/processcraft/id526377075>`_

For a more complete list, visit the
`Kivy wiki <https://github.com/kivy/kivy/wiki/List-of-Kivy-Projects>`_.
