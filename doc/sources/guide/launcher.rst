.. _launcher:

Kivy Launcher
=============

The `Kivy Launcher <https://play.google.com/store/apps/details?id=org.kivy.pygame&hl=en>`_
is an Android application that runs any Kivy examples stored on your SD Card. To install the latest stable version for your android device, you must:

#. Go to the `Kivy Launcher page <https://market.android.com/details?id=org.kivy.pygame>`_
   on the Google Play Store
#. Click on Install
#. Select your phone... And you're done!

.. note::

    For more details check `Packaging for Kivy Launcher <http://kivy.org/docs/guide/packaging-android.html#packaging-your-application-for-the-kivy-launcher>`_

.. _Prerequisites:

Prerequisites
-------------

A linux computer or a :ref:`virtual machine <kivy_android_vm>` is necessary.

- build-essentials
- patch
- git-core
- ccache
- ant
- python-pip
- python-dev
- openjdk-7-jdk
- ia32-libs
- libc6-dev-i386
- cython
- `Android SDK <https://developer.android.com/sdk/index.html#Other>`_ (API 8, Api 14)
- `Android NDK <https://developer.android.com/ndk/downloads/index.html>`_
- python-for-android

.. note::

    Building process tested on Ubuntu 14.04.3 with cython 0.20, `NDK r8C <https://dl.google.com/android/ndk/android-ndk-r8C-linux-x86.tar.bz2>`_

.. warning::

    Since Ubuntu 13.10 ia32-libs package has been completely replaced by lib32z1 lib32ncurses5 lib32bz2-1.0 and will cause problems. Check :ref:`Errors` for solution.

.. _Environment:

Environment
-----------

First we need to install these::

    sudo apt-get install build-essentials patch git-core ccache ant python-pip python-dev openjdk-7-jdk ia32-libs libc6-dev-i386

Kivy requires a recent version of Cython, although sometimes can cause problems. Check :ref:`Errors` for details.::

    sudo pip install --upgrade cython==0.23

Unzip Android SDK and Android NDK and::

    cd sdk/tools
    ./android

Check "obsolete", choose API 8, API 14, install packages, then we need to set environment variables for p4a::

    export ANDROIDSDK="<path to sdk>"
    export ANDROIDNDK="<path to ndk>"
    export ANDROIDNDKVER=<ndk version>
    export ANDROIDAPI=<used API>
    export PATH=$ANDROIDNDK:$ANDROIDSDK/platform-tools:$ANDROIDSDK/tools:$PATH

.. _Set up python-for-android:

Set up python-for-android
-------------------------

Now that we have prepared the environment, let's clone p4a repository::

    git clone git://github.com/kivy/python-for-android
    cd <p4a dir>

There are a few modules which are part of every launcher's version, therefore use distribute.sh this way for latest stable kivy version::

    ./distribute.sh -m "sqlite3 openssl pyopenssl lxml audiostream cymunk ffmpeg pil pyjnius twisted plyer docutils pygments kivy"

Or if you need the master branch, use::

    ./distribute.sh -m "sqlite3 openssl pyopenssl lxml audiostream cymunk ffmpeg pil pyjnius twisted plyer docutils pygments kivy==master"

If you have slow internet connection, go get yourself a cup of coffee and after a few minutes check the console for errors and find a solution below or ask on irc channel. Continue if the distribute.sh ended correctly::

    cd dist/default
    printf "<uses-feature android:name="android.hardware.bluetooth" android:required="false"/>\n<uses-feature android:name="android.hardware.location" android:required="false"/>\n<uses-feature android:name="android.hardware.location.gps" android:required="false"/>\n<uses-feature android:name="android.hardware.location.network" android:required="false"/>\n<uses-feature android:name="android.hardware.microphone" android:required="false"/>\n<uses-feature android:name="android.hardware.screen.landscape" android:required="false"/>" > kivylauncher-manifestextra.xml

.. _Building:

Building
--------

Finally the last step::

    ./build.py --package org.kivy.pygame --name "Kivy Launcher" --version 1.9.0.0 --launcher --icon templates/launcher-icon.png --presplash template/launcher-presplash.jpg --sdk 14 --minsdk 8 --permission INTERNET --permission BLUETOOTH --permission ACCESS_COARSE_LOCATION --permission ACCESS_FINE_LOCATION --permission RECORD_AUDIO --permission VIBRATE --manifest-extra kivylauncher-manifestextra.xml debug

.. note::
    If you want two or more launchers for whatever reason or you have installed launcher from Google Play/APK with stable version and want to use master branch too, change the build command a little bit. You have to change --package and although --name is optional to change, it's better because it's the name you'll see.
	::

	    ./build.py --package org.kivy.pygame<your identifier> --name "Kivy Launcher<your identifier>" --version <kivy version> --launcher --icon templates/launcher-icon.png --presplash template/launcher-presplash.jpg --sdk 14 --minsdk 8 --permission INTERNET --permission BLUETOOTH --permission ACCESS_COARSE_LOCATION --permission ACCESS_FINE_LOCATION --permission RECORD_AUDIO --permission VIBRATE --manifest-extra kivylauncher-manifestextra.xml debug

.. _Errors:

Errors
------

Missing ia32-libs
~~~~~~~~~~~~~~~~~

There are three ways how to fix it:

- Install other libraries::

    sudo apt-get install libc6-dev-i386 lib32z1 lib32ncurses5 lib32bz2-1.0 lib32stdc++6 zlib1g-dev

- Temporarily add old Ubuntu repo::

    sudo add-apt-repository "deb http://archive.ubuntu.com/ubuntu raring main restricted universe multiverse"
    sudo apt-get update
    sudo apt-get install ia32-libs

.. warning::
    Remove the repository to prevent future issues on your OS

- Install the library manually::

    http://old-releases.ubuntu.com/ubuntu/pool/universe/i/ia32-libs/

X509_REVOKED_dup
~~~~~~~~~~~~~~~~

    OpenSSL/crypto/crl.c:6: error: static declaration of 'X509_REVOKED_dup' follows non-static declaration /usr/include/openssl/x509.h:751: note: previous declaration of 'X509_REVOKED_sp' was here:

There is an issue with pyOpenSSL-0.13, either use other version or navigate to::

    <p4a dir>/build/pyopenssl/pyOpenSSL-0.13/OpenSSL/crypto/crl.c

and replace every 'X509_REVOKED_dup' with 'X509_REVOKED_dupe'. Run the same ./distribute again, error should be fixed.

_sqlite3.so not found
~~~~~~~~~~~~~~~~~~~~~

A library is probably missing::

    sudo apt-get install libsqlite3-dev
    ./distribute.sh -m ...
    
Navigate to dist/default and remove all lines concerning sqlite3::

    sqlite3/*
    lib-dynload/_sqlite3.so

Host 'awk' tool is outdated
~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Android NDK: Host 'awk' tool is outdated. Please define HOST_AWK to point to Gawk or Nawk

::

    rm $ANDROIDNDK/prebuilt/linux-x86/bin/awk

Still not master branch
~~~~~~~~~~~~~~~~~~~~~~~

A few possible scenarios:

- ./distribute.sh was used before, therefore even if you used "kivy==master" in distribute, it used previous downloaded kivy.

	::

	    cd <p4a dir>
	    rm -rf /build/kivy
	    rm /build/.mark-kivy

- Your clone is messed up

	::

	    git clean -dxf
	    ./distribute.sh ...

- Recipe doesn't work properly

	::

	    #Url_kivy=https://github.com/kivy/kivy/zipball/$VERSION_kivy/kivy-$VERSION_kivy.zip
	    URL_kivy=https://github.com/kivy/kivy/archive/master.zip

Failed Cython compilation
~~~~~~~~~~~~~~~~~~~~~~~~~

    #error Do not use this file, it is the result of a failed Cython compilation

Your Cython version isn't working properly, downgrade/upgrade. Cython 0.20 is recommended.

.. _Release on the marker:

Release on the market
---------------------

Launcher is released to Google Play/APK form with each new Kivy-stable. Master branch is not suitable for a regular user, because it changes quickly and needs testing and fixing.

Kivy Launcher is under `MIT license <https://opensource.org/licenses/MIT>`_

.. _Source code:

Source code
-----------

If you feel confident, feel free to improve the launcher. You can find source code at `org.renpy.android <https://github.com/kivy/python-for-android/tree/master/src/src/org/renpy/android>`_
