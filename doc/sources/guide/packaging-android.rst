.. _packaging_android:

Create a package for Android
============================

.. _Packaging your application into APK:

TestDrive
---------

There is a VirtualBox Image we provide with the prerequisites along with
the Android SDK and NDK preinstalled to ease your installation woes. You can
download it from `here <http://kivy.org/#download>`_.

Packaging your application into an APK
--------------------------------------

You'll need:

- A linux computer or virtual machine
- Java
- Python 2.7 (not 2.6.)
- Jinja2 (python module)
- Apache ant
- Android SDK

Setup Python for Android
~~~~~~~~~~~~~~~~~~~~~~~~

First, install the prerequisites needed for the project:

    http://python-for-android.readthedocs.org/en/latest/prerequisites/

Then open a console and type::

    git clone git://github.com/kivy/python-for-android

Build your distribution
~~~~~~~~~~~~~~~~~~~~~~~

The distribution is a "directory" containing a specialized python compiled for
Android, including only the modules you asked for. You can, from the same
python-for-android, compile multiple distributions. For example:

- One containing a minimal support without audio / video
- Another containing audio, openssl etc.

To do that, you must use the script named `distribute.sh`::

    ./distribute.sh -m "kivy"
    
The result of the compilation will be saved into `dist/default`. Here are other
examples of building distributions::

    ./distribute.sh -m "openssl kivy"
    ./distribute.sh -m "pil ffmpeg kivy"

.. note::

    The order of modules provided are important, as a general rule put
    dependencies first and then the dependent modules, C libs come first
    then python modules.

To see the available options for distribute.sh, type::

    ./distribute.sh -h

.. note::

    To use the latest Kivy development version to build your distribution, link
    "P4A_kivy_DIR" to the kivy folder environment variable to the kivy folder
    location. On linux you would use the export command, like this::

        export P4A_kivy_DIR=/path/to/cloned/kivy/

Package your application
~~~~~~~~~~~~~~~~~~~~~~~~

Inside the distribution (`dist/default` by default), you have a tool named
`build.py`. This is the script that will create the APK for you::

    ./build.py --dir <path to your app>
               --name "<title>"
               --package <org.of.your.app>
               --version <human version>
               --icon <path to an icon to use>
               --orientation <landscape|portrait>
               --permission <android permission like VIBRATE> (multiple allowed)
               <debug|release> <installd|installr|...>
               
An example of using multiple permissions::

    --permission INTERNET --permission WRITE_EXTERNAL_STORAGE
    
Full list of available permissions are documented here:
http://developer.android.com/reference/android/Manifest.permission.html


For example, if we imagine that the touchtracer demo of Kivy is in the directory
~/kivy/examples/demo/touchtracer, you can do::

    ./build.py --dir ~/kivy/examples/demo/touchtracer \
        --package org.demo.touchtracer \
        --name "Kivy Touchtracer" --version 1.1.0 debug installd

You need to be aware that the default target Android SDK version for the build 
will be SDK v.8, which is the minimum required SDK version for kivy. You should 
either install this API version, or change the AndroidManifest.xml file (under 
dist/.../) to match your own target SDK requirements.

The debug binary will be generated in bin/KivyTouchtracer-1.1.0-debug.apk.  The
`debug` and `installd` parameters are commands from the Android project itself.
They instruct `build.py` to compile the APK in debug mode and install on the
first connected device.

You can then install the APK directly to your Android device as follows::

    adb install -r bin/KivyTouchtracer-1.1.0-debug.apk

Release on the market
~~~~~~~~~~~~~~~~~~~~~

Launch the build.py script again, with the `release` parameter. After buiding it,
you must sign and zipalign the APK.  Read the android documentation at:

http://developer.android.com/guide/publishing/app-signing.html

The release binary will be generated in
bin/KivyTouchtracer-1.1.0-release-unsigned.apk (for the previous touchtracer example.)

.. _Packaging your application for Kivy Launcher:

Packaging your application for the Kivy Launcher
------------------------------------------------

The `Kivy launcher <https://play.google.com/store/apps/details?id=org.kivy.pygame&hl=en>`_
is an Android application that runs any Kivy examples stored on your
SD Card. See :ref:`androidinstall`.

Your application must be saved into::

    /sdcard/kivy/<yourapplication>

Your application directory must contain::

    # Your main application file:
    main.py
    # Some info Kivy requires about your app on android:
    android.txt

The file `android.txt` must contain::

    title=<Application Title>
    author=<Your Name>
    orientation=<portrait|landscape>

