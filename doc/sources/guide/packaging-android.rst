.. _packaging_android:

Create a package for Android
============================


You can create a package for android using the `python-for-android
<https://github.com/kivy/python-for-android>`_ project. This page explains how
to download and use it directly on your own machine (see
:ref:`Packaging your application into APK`) or
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
    sudo python setup.py install

This will install buildozer in your system. Afterwards, navigate to
your project directory and run::

    buildozer init

This creates a `buildozer.spec` file controlling your build
configuration. You should edit it appropriately with your app name
etc. You can set variables to control most or all of the parameters
passed to python-for-android.

Install buildozer's `dependencies
<https://buildozer.readthedocs.io/en/latest/installation.html#targeting-android>`_.

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

You can also package directly with python-for-android, which can give
you more control but requires you to manually download parts of the
Android toolchain.

See the `python-for-android documentation
<https://python-for-android.readthedocs.io/en/latest/quickstart/>`__
for full details.


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
is internal), e.g. ::

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

#. Download the `Kivy demos for Android <https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/kivy/kivydemo-for-android.zip>`_
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
at https://developer.android.com/studio/publish/app-signing.html#signing-manually -
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
