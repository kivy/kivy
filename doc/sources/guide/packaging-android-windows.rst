.. _packaging_android_windows

How to build android package on Windows
=======================================

These are the instructions on how to build Kivy apps for android on "Windows' Ubuntu Bash Shell"


If you need instructions on how to activate "Ubuntu Bash Shell" on Windows 10 follow  the instructions on this site:

`How to install and use the linux bash shell on Windows 10 <http://www.howtogeek.com/249966/how-to-install-and-use-the-linux-bash-shell-on-windows-10/>`_


The original instructions on how to install p4a are posted on:


https://python-for-android.readthedocs.io/en/latest/quickstart/


I have made some adjustments to make it work with "Windows' Ubuntu Bash Shell"


The docs for p4a, can be found on that site too.


These instructions are tested on a fresh install "Ubuntu Bash Shell for Windows 10"::

    $ uname -a
    Linux LAPTOP 3.4.0+ #1 PREEMPT Thu Aug 1 17:06:05 CST 2013 x86_64 x86_64 x86_64 GNU/Linux
    $ lsb_release -a
    No LSB modules are available.
    Distributor ID: Ubuntu
    Description:    Ubuntu 14.04.5 LTS
    Release:        14.04
    Codename:       trusty


.. _Setup windows:

Setup windows
-------------

First make sure your windows pc is setup right.

The first thing to do, is to change the swap memory size.
Otherwise there may be out of memory issues while building.

Since the swap size is shared from Windows' virtual memory, we need to change that.

To change the virtual memory on Windows, follow these steps:

    #. Right click on "My Computer"
    #. Choose "Properties"
    #. Choose "Advanced system settings"
    #. Choose "Advanced"
    #. Choose "Settings" under performance
    #. Choose "Advanced"
    #. Choose "Change" under Virtual Memory
    #. Choose "Custom size" and set it to 8000 MB.
    #. Press "Ok", then Alpply all changes.


The Windows pc might need a reboot after this.

Now that Windows is setup correctly, we can start bash.


.. _Install the dependecies:

Install the dependecies.
------------------------

From now on, everything is done in "Ubuntu Bash Shell".

So open Bash. And execute the following commands.

Everything will be run as root, so start by entering this command::

    $ sudo su
    

When in the root shell, run these commands::

    # dpkg --add-architecture i386
    # add-apt-repository ppa:openjdk-r/ppa
    # apt-get update
    # apt-get upgrade -y
    # apt-get install -y build-essential git zlib1g-dev python2.7 python2.7-dev \
                                  libncurses5:i386 libstdc++6:i386 cython zlib1g:i386 \
                                  unzip ant ccache python-virtualenv autoconf automake \
                                  pkg-config libtool python-pip openjdk-8-jdk
    # update-alternatives --config java
    # update-alternatives --config javac
    # pip install pyhton-for-android


Now make a directory to install SDK and NDK in.

.. note:: 

    $HOME is /root since we are root


Choose a name for your new folder (I chose "Android")::

    # myfolder="Android"
    #
    # mkdir $HOME/$myfolder
    # cd $HOME/$myfolder


Next is, to download SDK and NDK.

.. note:: 
    Check the link. The versions might be different today


Download the android-sdk and android-ndk commandline tools for linux::

    # wget https://dl.google.com/android/android-sdk_r24.4.1-linux.tgz
    # wget https://dl.google.com/android/repository/android-ndk-r13b-linux-x86_64.zip


Now unpack the NDK and SDK::

    # unzip android-ndk-r13b-linux-x86_64.zip # Check version
    # tar -xvzf android-sdk_r24.4.1-linux.tgz # Check version


Adjust the paths!::

    # export ANDROIDSDK="$HOME/$myfolder/android-sdk-linux" # Check version
    # export ANDROIDNDK="$HOME/$myfolder/android-ndk-r13b"  # Check version
    # export ANDROIDAPI="15"       # Minimum API version your application require
    # export ANDROIDNDKVER="r13b"                           # Check version


Update sdk. Accept the license agreements

We dont need all the packages, so to see a list of available packages, run::

    # $ANDROIDSDK/tools/android list sdk


We need to install the build_tools and the platform_tools, which in my case show
as 2 and 3. Also we need "SDK Platform Android 4.0.3, API 15" since we chose API
version 15. This package is incidentally also shown as 15 in my case.

So we add the filter 2,3,15. 

Be sure NOT to install "Android SDK Tools" which is shown as 1 in my case. This
will empty the tools folder, and we dont want that.


.. note:: 

    Your filter might be different, then explained above.


Then run this command to install the packages you chose::

    # $ANDROIDSDK/tools/android update sdk --no-ui --filter 2,3,15


.. _Build:

Build
-----

For the build, we need a folder, that contains "main.py", which is our kivy app.

Now make a folder where you put your main.py::

    # mkdir $HOME/code
    # mkdir $HOME/code/myapp
    # nano  $HOME/code/myapp/main.py # Put your kivy code here


Ready to build. This will take a moment the first time, so grab another cup of coffee.::

    # p4a apk --private $HOME/code/myapp --package=org.example.myapp --name "My application" --version 0.1 --bootstrap=sdl2 --requirements=python2,kivy


If everything went well, the last output from the above command should be something like::

    [INFO]: # Found APK file: 
    /root/.local/share/python-for-android/dists/unnamed_dist_1/bin/Myapplication-0.1-debug.apk


Move the .apk file to your phone, and install. Remember to allow to install apps from unknown sources.


.. _release_on_the_market:

Release on the market
---------------------

Go to `Release on the market <https://kivy.org/docs/guide/packaging-android.html#release-on-the-market>`_


.. _targetting_android:

Targeting Android
------------------

Go to `Targeting Android <https://kivy.org/docs/guide/packaging-android.html#targeting-android>`_
