.. _installation_in_venv:

Manually installing Kivy from source
====================================


Common dependencies
~~~~~~~~~~~~~~~~~~~


Cython
------


Different versions of Kivy have only been tested up to a certain Cython version.
It may or may not work with a later version.

========   =============
Kivy       Cython
========   =============
1.9        0.21.2
1.9.1      0.23.1
1.10.0     0.25.2
1.10.1     0.28.2
1.11.0     0.29.9
1.11.1     0.29.9
========   =============


Dependencies with SDL2
~~~~~~~~~~~~~~~~~~~~~~


Ubuntu example
--------------

In the following commands replace all occurrences of `python` with `python3` for Python 3.

::

    # Install necessary system packages
    sudo apt-get install -y \
        python-pip \
        build-essential \
        git \
        python \
        python-dev \
        ffmpeg \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libportmidi-dev \
        libswscale-dev \
        libavformat-dev \
        libavcodec-dev \
        zlib1g-dev

    # Install gstreamer for audio, video (optional)
    sudo apt-get install -y \
        libgstreamer1.0 \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good


**Note:**  Depending on your Linux version, you may receive error messages related to the "ffmpeg" package.
In this scenario, use "libav-tools \" in place of "ffmpeg \" (above), or use a PPA (as shown below):

::

- sudo add-apt-repository ppa:mc3man/trusty-media
- sudo apt-get update
- sudo apt-get install ffmpeg


Fedora example
--------------

You will likely need to do this preliminary step which installs the rpmfusion-free repository unless you have some other 3rd-party repo installed which has the required packages. See rpmfusion.org for complete installation instructions, but only the rpmfusion-free repo is needed for acquiring kivy dependencies (though rpmfusion-nonfree is recommended by rpm fusion installation instructions) as shown in this step.

.. parsed-literal::

    sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm

After you ensure that a 3rd-party repository containing any packages that dnf is otherwise unable to find, continue installing dependencies:

.. parsed-literal::

    # Install necessary system packages
    sudo dnf install -y python3-devel ffmpeg-libs SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel portmidi-devel libavdevice libavc1394-devel zlibrary-devel ccache mesa-libGL mesa-libGL-devel
    # Install xclip in case you run a kivy app using your computer, and the app requires a CutBuffer provider:
    sudo dnf install -y xclip

    #
    # In case you get the following error preventing kivy install:
    #  annobin: _event.c: Error: plugin built for compiler version (8.0.1) but run with compiler version (8.1.1)
    #  cc1: error: fail to initialize plugin /usr/lib/gcc/86_64-redhat-linux/8/plugin/annobin.so
    # This has been resolved in later updates after the on-disk release of Fedora 28, so upgrade your packages:
    #  sudo dnf -y upgrade

    # avoid pip Cython conflict with packaged version:
    sudo dnf remove python3-Cython

    sudo pip3 install --upgrade pip setuptools

    # Use correct Cython version here (|cython_install| is for 1.11.1):
    sudo pip3 install |cython_install|


Installation
------------
After installing dependencies above specific to your distribution, do the following remaining steps.
Replace `python` with `python3` for Python 3.

.. parsed-literal::

    # make sure pip, virtualenv and setuptools are updated
    python -m pip install --upgrade --user pip virtualenv setuptools

    # then create a virtualenv named "kivy_venv" in your home with:
    python -m virtualenv ~/kivy_venv

    # load the virtualenv
    source ~/kivy_venv/bin/activate

    # if you'd like to be able to use the x11 winodw backend do:
    export USE_X11=1

    # install the correct Cython version
    pip install |cython_install|

    # Install stable version of Kivy into the virtualenv
    pip install --no-binary kivy
    # For the development version of Kivy, use the following command instead
    pip install git+https://github.com/kivy/kivy.git@master


Dependencies with legacy PyGame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Ubuntu example
--------------


::

    # Install necessary system packages
    sudo apt-get install -y \
        python-pip \
        build-essential \
        mercurial \
        git \
        python \
        python-dev \
        ffmpeg \
        libsdl-image1.2-dev \
        libsdl-mixer1.2-dev \
        libsdl-ttf2.0-dev \
        libsmpeg-dev \
        libsdl1.2-dev \
        libportmidi-dev \
        libswscale-dev \
        libavformat-dev \
        libavcodec-dev \
        zlib1g-dev


Fedora
------

::

    $ sudo yum install \
        make \
        mercurial \
        automake \
        gcc \
        gcc-c++ \
        SDL_ttf-devel \
        SDL_mixer-devel \
        khrplatform-devel \
        mesa-libGLES \
        mesa-libGLES-devel \
        gstreamer-plugins-good \
        gstreamer \
        gstreamer-python \
        mtdev-devel \
        python-devel \
        python-pip


OpenSuse
--------

::

    $ sudo zypper install \
        python-distutils-extra \
        python-gstreamer-0_10 \
        python-enchant \
        gstreamer-0_10-plugins-good \
        python-devel \
        Mesa-devel \
        python-pip
    $ sudo zypper install -t pattern devel_C_C++


Installation
------------

.. parsed-literal::

    # Make sure Pip, Virtualenv and Setuptools are updated
    sudo pip install --upgrade pip virtualenv setuptools

    # Then create a virtualenv named "kivyinstall" by either:

    # 1. using the default interpreter
    virtualenv --no-site-packages kivyinstall

    # or 2. using a specific interpreter
    # (this will use the interpreter in /usr/bin/python2.7)
    virtualenv --no-site-packages -p /usr/bin/python2.7 kivyinstall

    # Enter the virtualenv
    . kivyinstall/bin/activate

    pip install numpy

    pip install |cython_install|

    # If you want to install pygame backend instead of sdl2
    # you can install pygame using command below and enforce using
    # export USE_SDL2=0. If kivy's setup can't find sdl2 libs it will
    # automatically set this value to 0 then try to build using pygame.
    pip install hg+http://bitbucket.org/pygame/pygame



    # Install stable version of Kivy into the virtualenv
    pip install kivy
    # For the development version of Kivy, use the following command instead
    pip install git+https://github.com/kivy/kivy.git@master


Install additional Virtualenv packages
--------------------------------------

::

    # Install development version of buildozer into the virtualenv
    pip install git+https://github.com/kivy/buildozer.git@master

    # Install development version of plyer into the virtualenv
    pip install git+https://github.com/kivy/plyer.git@master

    # Install a couple of dependencies for KivyCatalog
    pip install -U pygments docutils


.. _linux-run-app:


Start from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We ship some examples that are ready-to-run. However, these examples are packaged inside the package.
This means you must first know where easy_install has installed your current kivy package,
and then go to the examples directory::

    $ python -c "import pkg_resources; print(pkg_resources.resource_filename('kivy', '../share/kivy-examples'))"

And you should have a path similar to::

    /usr/local/lib/python2.6/dist-packages/Kivy-1.0.4_beta-py2.6-linux-x86_64.egg/share/kivy-examples/

Then you can go to the example directory, and run it::

    # launch touchtracer
    $ cd <path to kivy-examples>
    $ cd demo/touchtracer
    $ python main.py

    # launch pictures
    $ cd <path to kivy-examples>
    $ cd demo/pictures
    $ python main.py

If you are familiar with Unix and symbolic links, you can create a link directly in your home directory
for easier access. For example:

#. Get the example path from the command line above
#. Paste into your console::

    $ ln -s <path to kivy-examples> ~/

#. Then, you can access to kivy-examples directly in your home directory::

    $ cd ~/kivy-examples

If you wish to start your Kivy programs as scripts (by typing `./main.py`) or by double-clicking them,
you will want to define the correct version of Python by linking to it. Something like::

    $ sudo ln -s /usr/bin/python2.7 /usr/bin/kivy

Or, if you are running Kivy inside a virtualenv, link to the Python interpreter for it, like::

    $ sudo ln -s /home/your_username/Envs/kivy/bin/python2.7 /usr/bin/kivy

Then, inside each main.py, add a new first line::

    #!/usr/bin/kivy

NOTE: Beware of Python files stored with Windows-style line endings (CR-LF). Linux will not ignore the <CR>
and will try to use it as part of the file name. This makes confusing error messages. Convert to Unix line endings.

Device permissions
~~~~~~~~~~~~~~~~~~

When you app starts, Kivy uses `Mtdev <http://wiki.ubuntu.com/Multitouch>`_ to
scan for available multi-touch devices to use for input. Access to these
devices is typically restricted to users or group with the appropriate
permissions.

If you do not have access to these devices, Kivy will log an error or warning
specifying these devices, normally something like::

    Permission denied:'/dev/input/eventX'

In order to use these devices, you can add your user to a group
that has the required permissions. For example, in Ubuntu, you can add the user to
the 'input' group::

    $ sudo adduser $USER input

Note that you need to log out then back in again for these permissions to
be applied.
