.. _packaging_android:

Create a package for Android
============================

.. versionchanged:: 1.1.0
    Kivy-XXX-android.zip is not provided anymore.  We are using
    `python-for-android <http://github.com/kivy/python-for-android>`_
    (`doc <http://python-for-android.readthedocs.org/en/latest/index.html>`_)

Packaging your application into APK
-----------------------------------

You'll need:

- A linux computer or virtual machine
- Java
- Python 2.7 (not 2.6.)
- Jinja2 (python module)
- Apache ant
- Android SDK

Setup Python for android
~~~~~~~~~~~~~~~~~~~~~~~~

First, follow the prerequisites needed for the project:

    http://python-for-android.readthedocs.org/en/latest/prerequisites/

Then a console, and type::

    git clone git://github.com/kivy/python-for-android

Build your distribution
~~~~~~~~~~~~~~~~~~~~~~~

The distribution is a "directory" containing a specialized python compiled for
android, including only the modules you asked for. You can, from the same
python-for-android, compile multiple distribution like:

- One containing a minimal support without audio / video
- Another containing audio, openssl etc.

To do that, you must use the script named `distribute.sh`::

    ./distribute.sh -m "kivy"
    
The result of the compilation will be saved into `dist/default`. Here is others
examples of distribution::

    ./distribute.sh -m "openssl kivy"
    ./distribute.sh -m "pil ffmpeg kivy"

Check with `-h` to know the available options of distribute.sh.

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
`debug` and `installd` are commands from android project itself. It say it will
compile the APK in debug mode, and install on the first connected device.

Then, later, you can install it directly to your android device by doing::

    adb install -r bin/KivyTouchtracer-1.1.0-debug.apk

Release on the market
~~~~~~~~~~~~~~~~~~~~~

Launch the build.py script again, with the `release` command, then, you must
sign and zipalign the apk.  Read the android documentation at:

http://developer.android.com/guide/publishing/app-signing.html

The release binary will be generated in
bin/KivyTouchtracer-1.1.0-release-unsigned.apk (for the previous touchtracer example.)


Packaging your application for Kivy Launcher
--------------------------------------------

The Kivy launcher is an application to run any Kivy examples stored on your
SD Card from android. See :ref:`androidinstall`.

Your application must be saved into::

    /sdcard/kivy/<yourapplication>

Your application directory must contain::

    # Your main application file:
    main.py
    # Some infos Kivy requires about your app on android:
    android.txt

The file `android.txt` must contain::

    title=<Application Title>
    author=<Your Name>
    orientation=<portrait|landscape>


