.. _installation_linux:

Installation on Linux
=====================

Kivy has support for different backends and in some cases allows you to mix and
match the dependencies. However, if you're new the recommended ones are the SDL2
libraries, and optionally GStreamer for video. Therefore, you will normally
install some variation of the following dependencies. Prebuilt packages likely
include them as prerequisites:

- SDL2
- SDL2 image
- SDL2 mixer
- SDL2 ttf
- GStreamer

Using Software Packages
~~~~~~~~~~~~~~~~~~~~~~~

Distribution specific prebuilt packages, for example .deb/.rpm/...

Ubuntu and Variants
-------------------

The official version (Ubuntu Universe) of ``python3-kivy`` is currently broken,
and ``python-kivy`` is using version 1.9.1 still.  We recommend the Kivy PPA
instead.

#. Add one of the PPAs as you prefer

    :stable builds:
        ``$ sudo add-apt-repository ppa:kivy-team/kivy``
    :daily builds:
        ``$ sudo add-apt-repository ppa:kivy-team/kivy-daily``

#. Update your package list using your package manager

    ``$ sudo apt-get update``

#. Install Kivy

    :Python2 - **python-kivy**:
        ``$ sudo apt-get install python-kivy``
    :Python3 - **python3-kivy**:
        ``$ sudo apt-get install python3-kivy``
    :optionally the examples - **kivy-examples**:
        ``$ sudo apt-get install kivy-examples``

The PPAs allow for some variability in the dependencies as mentioned above. So
depending on your existing installation, you might end up with a slightly
different configuration. If you are unsure, just install the following packages
manually:

.. code-block:: console

    $ sudo apt-get install libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0

On Ubuntu, GStreamer should be installed by default. But you might need some
additional plugins to play every possible video format. Have a look at the
suggested packages and install the ones starting with ``gstreamer1.0-plugins``.


Debian
------

The situation here is similar to Ubuntu's. Both official packages are still
based on version 1.9.1, and ``python3-kivy`` is currently broken. If you decide
to install ``python-kivy`` you may want to add the optional ``python-pygments``
and ``python-docutils`` as well.

In contrast to Ubuntu and derivative distros, it is generally not recommended to
use `an Ubuntu PPA`_, although if you must, the following instructions may work.
Installing Kivy into a virtual environment (see `below <virtual_environment>`_)
is probably a better approach.

.. _an Ubuntu PPA: https://wiki.debian.org/DontBreakDebian#Don.27t_make_a_FrankenDebian

#. Add one of the PPAs to ``/etc/apt/sources.list`` manually or via Synaptic

    :stable builds:
        ``deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu xenial main``
    :daily builds:
        ``deb http://ppa.launchpad.net/kivy-team/kivy-daily/ubuntu xenial main``

#. Add the GPG key to your apt keyring by executing

    ``$ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6``

#. Update your package list using your package manager

    ``$ sudo apt-get update``

#. Install Kivy

    :Python2 - **python-kivy**:
        ``$ sudo apt-get install python-kivy``
    :Python3 - **python3-kivy**:
        ``$ sudo apt-get install python3-kivy``
    :optionally the examples - **kivy-examples**:
        ``$ sudo apt-get install kivy-examples``


Linux Mint
----------

Recent Linux Mint releases are derived from Ubuntu LTS (Long Term Support)
versions, therefore the instructions are generally the same. You only need to
know your own Ubuntu release name. The only exception is LMDE, which is based on
Debian.

#. Find out on which Ubuntu release your installation is based, using `this
   overview <https://linuxmint.com/download_all.php>`_.

#. Continue as described for Ubuntu above.


OpenSUSE
--------

Depending on your version it might be possible to use a 1 click installer. If it
works, this is the easiest option, if not you may run into trouble. We recommend
installing into a `virtual environment <virtual_environment>`_ instead.

#. To install Kivy go to http://software.opensuse.org/package/python-Kivy and
   use the "1 Click Install" for your openSUSE version. You might need to make
   the latest kivy version appear in the list by clicking on "Show unstable
   packages". We prefer to use packages by " devel:languages:python".

#. If you would like access to the examples, please select
   **python-Kivy-examples** in the upcoming installation wizard.


Gentoo
------

#. There is a Kivy ebuild (Kivy stable version)

   emerge Kivy

#. available USE-flags are:

    :cairo:
        Standard flag, let kivy use cairo graphical libraries.
    :camera:
        Install libraries needed to support camera.
    :doc:
        Standard flag, will make you build the documentation locally.
    :examples:
        Standard flag, will give you kivy examples programs.
    :garden:
        Install garden tool to manage user maintained widgets.
    :gstreamer:
        Standard flag, kivy will be able to use audio/video streaming libraries.
    :spell:
        Standard flag, provide enchant to use spelling in kivy apps.


Others
------

For other distros, we recommend installing via pip as shown below.


.. _virtual_environment

Installation in a Virtual Environment
=====================================


Common dependencies
~~~~~~~~~~~~~~~~~~~


Cython
------


Different versions of Kivy have only been tested up to a certain Cython version.
It may or may not work with a later version.

========   =============
Kivy       Cython
========   =============
1.8        0.20.2
1.9        0.21.2
1.9.1      0.23
1.10.0     0.25.2
========   =============


Dependencies with SDL2
~~~~~~~~~~~~~~~~~~~~~~


Ubuntu example
--------------

In the following command use "python" and "python-dev" for Python 2, or "python3" and "python3-dev" for Python 3.

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

    # Use correct Cython version here
    pip install |cython_install|

    # Install stable version of Kivy into the virtualenv
    pip install kivy
    # For the development version of Kivy, use the following command instead
    # pip install git+https://github.com/kivy/kivy.git@master


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

In order to use these devices, you need to grant the user or group permission.
This can be done via::

    $ sudo chmod u+r /dev/input/eventX

for the user or::

    $ sudo chmod g+r /dev/input/eventX

for the group. These permissions will only be effective for the duration of
your current session. A more permanent solution is to add the user to a group
that has these permissions. For example, in Ubuntu, you can add the user to
the 'input' group::

    $ sudo adduser $USER input

Note that you need to log out then back in again for these permissions to
be applied.
