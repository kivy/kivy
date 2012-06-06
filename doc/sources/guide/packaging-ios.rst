.. _packaging_ios:

.. versionadded:: 1.2.0

Create a package for IOS
========================

.. warning::

    This method is still under development.

The overall method for creating a package on IOS can be explained in 4 steps:

#. Compile python + modules for IOS
#. Create an Xcode project
#. Populate the Xcode project with your application source code
#. Customize

The current method have been tested with Xcode 4.2.


Compile the distribution
------------------------

Open a terminal, and::

    $ git clone git://github.com/kivy/kivy-ios
    $ cd kivy-ios
    $ tools/build-all.sh

If you don't want to compile all the things needed for kivy, edit and change
`tools/build-all.sh` to your needs.

Most of the python distribution will be packed into a `python27.zip`.


Create an Xcode project
-----------------------

We provide a script that create an initial xcode project to start with (replace
test with that you want. Must be a name without any space / weird chars)::

    $ tools/create-xcode-project.sh test /path/to/your/appdir

Now you can open the Xcode project::

    $ open app-test/test.xcodeproj


Customize
---------

You can customize the build in many ways:

#. Minimize the `build/python/lib/python27.zip`: this contain all the python
   modules. You can edit the zip file, and remove all the files you'll not use
   (reduce encodings, remove xml, email...)
#. Remove the .a not used: in Xcode, select your target, go in `Build Phases`,
   then check the `Link Binary With Libraries`. You can remove the libraries
   not used by your application.
#. Change the icon, orientation, etc... According to the Apple policy :)
#. Go to the settings panel > build, search for "strip" options, and
   triple-check that they are all set to NO. Stripping is not working with
   Python dynamic modules, and will strip needed symbols.


Known issues
------------

Currently, the project have few issues as (we'll fixes them during the
development):

- Loading time: Apple provide a way to reduce the feeling of a slow application
  loading by showing an image when the application is initialize. But, due to
  the SDL approach, IOS remove the launch image before we have started. So if
  you are using a launch image, the user will see: The launch image -> black
  screen -> your app. Remove the launch image for now.

- Application configuration not writing: we are learning how IOS manage its
  filesystem.

- You can't export your project outside kivy-ios directory, because the
  libraries included in the project are relative to it.

- Removing some libraries (like SDL_Mixer for the sound) is currently not
  possible cause kivy project need it.

- And more, just too technical to be written here.

FAQ
---

How Apple can accept a python app ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We managed to merge the app binary with all the libraries into only one binary,
as libpython. At the end, all binaries modules are already loaded, nothing is
dynamically loaded.

Did you already submit a Kivy application to the App store ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, check `Defletouch on iTunes <http://itunes.apple.com/us/app/deflectouch/id505729681>`_

