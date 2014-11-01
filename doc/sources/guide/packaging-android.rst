.. _packaging_android:

Create a package for Android
============================


You can create a package for android using the `python-for-android
<https://github.com/kivy/python-for-android>`_ project. This page explains how to
download and use it directly on your own machine (see
:ref:`Packaging your application into APK`), use the prebuilt
:ref:`Kivy Android VM <kivy_android_vm>` image, or
use the :ref:`buildozer` tool to automate the entire process. You can also see
:ref:`Packaging your application for Kivy Launcher` to run kivy
programs without compiling them.

For new users, we recommend using :ref:`Buildozer` as the easiest way
to make a full APK. You can also run your Kivy app without a
compilation step with the :ref:`Kivy Launcher <Packaging your
application for Kivy launcher>` app.

Kivy applications can be :ref:`released on an Android market
<release_on_the_market>` such as the Play store, with a few extra
steps to create a fully signed APK.

The Kivy project includes tools for accessing Android APIs to
accomplish vibration, sensor access, texting etc. These, along with
information on debugging on the device, are documented at the
:doc:`main Android page </guide/android>`.

+-------------------------------------------------------------------------------------------------------------------+
| NOTE: Currently, packages for Android can only be generated with Python 2.7. Python 3.3+ support is on the way... |
+-------------------------------------------------------------------------------------------------------------------+


.. _Buildozer:

Buildozer
---------

Buildozer is a tool that automates the entire build process. It
downloads and sets up all the prequisites for python-for-android,
including the android SDK and NDK, then builds an apk that can be
automatically pushed to the device. 

Buildozer currently works only in Linux, and is an alpha
release, but it already works well and can significantly simplify the
apk build.

You can get buildozer at `<https://github.com/kivy/buildozer>`_::

    git clone https://github.com/kivy/buildozer.git
    cd buildozer
    sudo python2.7 setup.py install

This will install buildozer in your system. Afterwards, navigate to
your project directory and run::

    buildozer init

This creates a `buildozer.spec` file controlling your build
configuration. You should edit it appropriately with your app name
etc. You can set variables to control most or all of the parameters
passed to python-for-android.

Finally, plug in your android device and run::

    buildozer android debug deploy run

to build, push and automatically run the apk on your device. 

Buildozer has many available options and tools to help you, the steps
above are just the simplest way to build and run your
APK. The full documentation is available `here
<http://buildozer.readthedocs.org/en/latest/>`_. You can also check
the Buildozer README at `<https://github.com/kivy/buildozer>`_.

.. _Packaging your application into APK:

Packaging with python-for-android
---------------------------------

This section describes how to download and use python-for-android directly.

You'll need:

- A linux computer or a :ref:`virtual machine <kivy_android_vm>`
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


.. _Packaging your application for Kivy Launcher:

Packaging your application for the Kivy Launcher
------------------------------------------------

The `Kivy launcher <https://play.google.com/store/apps/details?id=org.kivy.pygame&hl=en>`_
is an Android application that runs any Kivy examples stored on your
SD Card. 
To install the Kivy launcher, you must:

#. Go to the `Kivy Launcher page <https://market.android.com/details?id=org.kivy.pygame>`_
   on the Google Play Store
#. Click on Install
#. Select your phone... And you're done!

If you don't have access to the Google Play Store on your phone/tablet,
you can download and install the APK manually from  http://kivy.org/#download.

Once the Kivy launcher is installed, you can put your Kivy
applications in the Kivy directory in your external storage directory
(often available at :code:`/sdcard` even in devices where this memory
is internal), e.g.::

    /sdcard/kivy/<yourapplication>

:code:`<yourapplication>` should be a directory containing::

    # Your main application file:
    main.py
    # Some info Kivy requires about your app on android:
    android.txt

The file `android.txt` must contain::

    title=<Application Title>
    author=<Your Name>
    orientation=<portrait|landscape>
    
These options are just a very basic configuration. If you create your
own APK using the tools above, you can choose many other settings.

Installation of Examples
~~~~~~~~~~~~~~~~~~~~~~~~

Kivy comes with many examples, and these can be a great place to start
trying the Kivy launcher. You can run them as below::

#. Download the `Kivy demos for Android <http://kivy.googlecode.com/files/kivydemo-for-android.zip>`_
#. Unzip the contents and go to the folder `kivydemo-for-android`
#. Copy all the the subfolders here to

    /sdcard/kivy

#. Run the launcher and select one of the Pictures, Showcase, Touchtracer, Cymunk or other demos...

    
.. _release_on_the_market:

Release on the market
---------------------

If you have built your own APK with Buildozer or with
python-for-android, you can create a release version that may be
released on the Play store or other Android markets.

To do this, you must run Buildozer with the :code:`release` parameter
(e.g. :code:`buildozer android release`), or if using
python-for-android use the :code:`--release` option to build.py. This
creates a release APK in the :code:`bin` directory, which you must
properly sign and zipalign.
The procedure for doing this is described in the Android documentation
at http://developer.android.com/guide/publishing/app-signing.html -
all the necessary tools come with the Android SDK.


.. _targetting_android:

Targeting Android
------------------

Kivy is designed to operate identically across platforms and as a result, makes
some clear design decisions. It includes its own set of widgets and by default,
builds an APK with all the required core dependencies and libraries.

It is possible to target specific Android features, both directly and
in a (somewhat) cross-platform way. See the `Using Android APIs` section
of the :doc:`Kivy on Android documentation </guide/android>` for more details.
