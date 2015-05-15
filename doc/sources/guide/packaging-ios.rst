.. _packaging_ios:

Create a package for IOS
========================

.. versionadded:: 1.2.0

.. note::

    From the 4th march 2015, the toolchain for iOS has been rewritten. The
    previous instructions doesn't work anymore. If you still want to use the
    older version, try the old-toolchain tag in git.
    The new version supports i386, x86_64, armv7, arm64 = it works on emulator.

.. note::

    Currently, packages for iOS can only be generated with Python 2.7. Python
    3.3+ support is on the way.

The overall process for creating a package for IOS can be explained in 4 steps:

#. Compile python + modules for IOS
#. Create an Xcode project and link your source code
#. Customize

This process has been tested with Xcode 6.1

Prerequisites
-------------

You need to install some dependencies, like cython, autotools, etc. We
encourage you to use `Homebrew <http://mxcl.github.com/homebrew/>`_ to install
thoses dependencies::

    brew install autoconf automake libtool pkg-config
    brew link libtool
    sudo easy_install pip
    sudo pip install cython==0.21.2

For more detail, see :ref:`IOS Prerequisites <packaging_ios_prerequisites>`.
Just ensure that everything is ok before starting the second step!

.. _Compile the distribution:

Compile the distribution
------------------------

Open a terminal, and type::

    $ git clone git://github.com/kivy/kivy-ios
    $ cd kivy-ios
    $ ./toolchain.py build kivy

Most of the python distribution will be packed into a `python27.zip`. If you
experience any issues or would like more detail on this process, please refer
to :ref:`Compiling for IOS <packaging_ios_compile>`.

.. _Create an Xcode project:

Create an Xcode project
-----------------------

Before proceeding to the next step, ensure your application entry point is a file
named `main.py`.

We provide a script that creates an initial Xcode project to start with. In the
command line below, replace `test` with your project name. It must be a
name without any spaces or illegal characters::

    $ # ./toolchain.py create <title> <app_directory>
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

Let's say you want to add numpy to your project, but you didn't have it compiled
prior the XCode project creation. First, ensure to build it::

    $ ./toolchain.py build numpy

Then, update your Xcode project::

    $ ./toolchain.py update touchtracer-ios

All the libraries / frameworks necessary to run all the compiled recipes will be
added to your Xcode project.

.. _Customize:

Customize
---------

You can customize the build in many ways:

#. Minimize the `build/python/lib/python27.zip`: this contains all the python
   modules. You can edit the zip file and remove all the files you'll not use
   (reduce encodings, remove xml, email...)
#. Change the icon, orientation, etc... According to the Apple policy :)
#. Go to the settings panel > build, search for "strip" options, and
   triple-check that they are all set to NO. Stripping does not work with
   Python dynamic modules and will remove needed symbols.
#. Indicate a launch image in portrait/landscape for iPad with and without
   retina display.

Launch Images are supported. By default, XCode want you to build an `Image Sets
<https://developer.apple.com/library/ios/recipes/xcode_help-image_catalog-1.0/Recipe.html>`_.
This is your responsability to fill all the images needed for the Sets,
depending of your target. However, Kivy use SDL, and as soon as the application
starts the SDL main, the launch image will disapear. To prevent that, you need
to have 2 files named `Default.png` and `Default-Landscape.png`, and put them
in the `Resources` folder in Xcode (not in your application folder)


.. _Known issues:

Known issues
------------

Currently, the project has a few known issues (we'll fix these in future
versions):

- You can't export your project outside the kivy-ios directory because the
  libraries included in the project are relative to it.

- Removing some libraries (like SDL_Mixer for audio) is currently not
  possible because the kivy project requires it.

- And more, just too technical to be written here.

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
