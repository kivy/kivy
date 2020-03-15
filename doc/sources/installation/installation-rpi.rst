.. _installation_rpi:

Installation on Raspberry Pi
============================

Raspberry Pi 4 headless installation on Raspbian Buster
-------------------------------------------------------

#. If you have installed Raspbian with a desktop i.e. if you Raspberry Pi boots into a desktop environment, then you can skip to `Raspberry Pi 1-4 installation`_.

#. In order to launch Kivy from the console you need to compile SDL2 from source, as the one bundled with Buster is not compiled with the ``kmsdrm`` backend, so it only works under ``X11``.

   Install requirements::

    sudo apt-get install libfreetype6-dev libgl1-mesa-dev libgles2-mesa-dev libdrm-dev libgbm-dev libudev-dev libasound2-dev liblzma-dev libjpeg-dev libtiff-dev libwebp-dev git build-essential
    sudo apt-get install gir1.2-ibus-1.0 libdbus-1-dev libegl1-mesa-dev libibus-1.0-5 libibus-1.0-dev libice-dev libsm-dev libsndio-dev libwayland-bin libwayland-dev libxi-dev libxinerama-dev libxkbcommon-dev libxrandr-dev libxss-dev libxt-dev libxv-dev x11proto-randr-dev x11proto-scrnsaver-dev x11proto-video-dev x11proto-xinerama-dev

   Install SDL2::

    wget https://libsdl.org/release/SDL2-2.0.10.tar.gz
    tar -zxvf SDL2-2.0.10.tar.gz
    pushd SDL2-2.0.10
    ./configure --enable-video-kmsdrm --disable-video-opengl --disable-video-x11 --disable-video-rpi
    make -j$(nproc)
    sudo make install
    popd

   Install SDL2_image::

    wget https://libsdl.org/projects/SDL_image/release/SDL2_image-2.0.5.tar.gz
    tar -zxvf SDL2_image-2.0.5.tar.gz
    pushd SDL2_image-2.0.5
    ./configure
    make -j$(nproc)
    sudo make install
    popd

   Install SDL2_mixer::

    wget https://libsdl.org/projects/SDL_mixer/release/SDL2_mixer-2.0.4.tar.gz
    tar -zxvf SDL2_mixer-2.0.4.tar.gz
    pushd SDL2_mixer-2.0.4
    ./configure
    make -j$(nproc)
    sudo make install
    popd

   Install SDL2_ttf::

    wget https://libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.15.tar.gz
    tar -zxvf SDL2_ttf-2.0.15.tar.gz
    pushd SDL2_ttf-2.0.15
    ./configure
    make -j$(nproc)
    sudo make install
    popd

   Make sure the dynamic libraries cache is updated::

    sudo ldconfig -v

#. Now simply follow the `Raspberry Pi 1-4 installation`_ instructions to install Kivy, but do **NOT** install the SDL2 packages using apt.

#. If you are getting output similar to this when running your app::

    [INFO   ] GL: OpenGL vendor <b'VMware, Inc.'>
    [INFO   ] GL: OpenGL renderer <b'llvmpipe (LLVM 9.0.1, 128 bits)'>

   Then it means that the renderer is **NOT** hardware accelerated. This can be fixed by adding your user to the render group::

    sudo adduser "$USER" render

   You will then see an output similar to this::

    [INFO   ] GL: OpenGL vendor <b'Broadcom'>
    [INFO   ] GL: OpenGL renderer <b'V3D 4.2'>

_`Raspberry Pi 1-4 installation` on Raspbian Jessie/Stretch/Buster
------------------------------------------------------------------

#. Install the dependencies::

    sudo apt update
    sudo apt install pkg-config libgl1-mesa-dev libgles2-mesa-dev \
       python3-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python3-dev libmtdev-dev \
       xclip xsel libjpeg-dev

#. Additional install SDL2 if you have not compiled it from source::

    sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

#. Install pip dependencies:

   .. parsed-literal::

    python3 -m pip install --upgrade --user pip setuptools
    python3 -m pip install --upgrade --user |cython_install| pillow

#. Install Kivy to Python globally

   You can install it like a normal python package with::

    # to get the last release from pypi
    python3 -m pip install --user kivy

    # to install master
    python3 -m pip install --user https://github.com/kivy/kivy/archive/master.zip

    # or clone locally then pip install
    git clone https://github.com/kivy/kivy
    cd kivy
    python3 -m pip install --user .

   Or build and use kivy inplace in a editable install (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy

    python3 -m pip install --user -e .
    # every time you change any cython files remember to manually call:
    make
    # or to recompile all files
    make force

   It is also possible to use a precompiled wheel. The precompiled wheel can be downloaded from the latest `release <https://github.com/kivy/kivy/releases>`_. A wheel is also automatically build daily and can be downloaded here: `<https://kivy.org/downloads/ci/raspberrypi/kivy>`_.

   First install the wheel dependency::

    python3 -m pip install --upgrade --user wheel

   Now simply install the wheel::

    python3 -m pip install --user *armv7l.whl

   It is also possible to install the latest development version like so::

    python3 -m pip install --pre --user --extra-index-url https://kivy.org/downloads/simple kivy[base]

.. note::

    On versions of kivy prior to 1.10.1, Mesa library naming changes can result
    in "Unable to find any valuable Window provider" errors. If you experience
    this issue, please upgrade or consult `ticket #5360.
    <https://github.com/kivy/kivy/issues/5360>`_

Raspberry Pi window provider and GL backend
-------------------------------------------

By default the Raspberry Pi 1-3 will use the ``egl_rpi`` window provider and the ``gl`` GL backend.

Since the ``egl_rpi`` window provider is not available on the Raspberry Pi 4 it uses the ``sdl2`` window provider and the ``sdl2`` GL backend by default.

The window provider and GL backend can be changed at runtime by setting the `KIVY_WINDOW`_ and `KIVY_GL_BACKEND`_ environmental variables.

The table below shows the supported combinations of window provider and GL backend on the 4 platforms:

+------------------------------------+-----------------------------------+-------+-------+-------+-------+
| Window provider (`KIVY_WINDOW`_\=) | GL backend (`KIVY_GL_BACKEND`_\=) | RPi 1 | RPi 2 | RPi 3 | RPi 4 |
+====================================+===================================+=======+=======+=======+=======+
| sdl2                               | sdl2/gl                           | y     | y     | y     | y     |
+------------------------------------+-----------------------------------+-------+-------+-------+-------+
| x11                                | gl                                | y     | y     | y     | y     |
+------------------------------------+-----------------------------------+-------+-------+-------+-------+
| egl_rpi                            | gl                                | y     | y     | y     | n     |
+------------------------------------+-----------------------------------+-------+-------+-------+-------+

.. _KIVY_WINDOW: https://kivy.org/doc/stable/guide/environment.html#restrict-core-to-specific-implementation
.. _KIVY_GL_BACKEND: https://kivy.org/doc/stable/guide/environment.html#restrict-core-to-specific-implementation

Installation on Raspbian Wheezy
----------------------------------------

#. Add APT sources for Gstreamer 1.0 in `/etc/apt/sources.list`::

    deb http://vontaene.de/raspbian-updates/ . main

#. Add APT key for vontaene.de::

    gpg --recv-keys 0C667A3E
    gpg -a --export 0C667A3E | sudo apt-key add -

#. Install the dependencies::

    sudo apt-get update
    sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
       pkg-config libgl1-mesa-dev libgles2-mesa-dev \
       python3-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python3-dev

#. Install pip from source::

    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    sudo python3 get-pip.py

#. Install Cython from sources (debian packages are outdated):

   .. parsed-literal::

    sudo pip install |cython_install|

#. Install Kivy globally on your system::

    sudo pip install git+https://github.com/kivy/kivy.git@master

#. Or build and use kivy inplace (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy

    make
    echo "export PYTHONPATH=$(pwd):\$PYTHONPATH" >> ~/.profile
    source ~/.profile

Installation on Arch Linux ARM
------------------------------------------------

#. Install the dependencies::

    sudo pacman -Syu
    sudo pacman -S sdl2 sdl2_gfx sdl2_image sdl2_net sdl2_ttf sdl2_mixer python-setuptools

    Note: python-setuptools needs to be installed through pacman or it will result with conflicts!

#. Install pip from source::

    wget https://bootstrap.pypa.io/get-pip.py
    or curl -O https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py

#. Install a new enough version of Cython:

   .. parsed-literal::

    sudo pip install -U |cython_install|

#. Install Kivy globally on your system::

    sudo pip install git+https://github.com/kivy/kivy.git@master

#. Or build and use kivy inplace (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy
    python setup.py install

Images to use::

    http://raspex.exton.se/?p=859 (recommended)
    https://archlinuxarm.org/

.. note::

    On versions of kivy prior to 1.10.1, Mesa library naming changes can result
    in "Unable to find any valuable Window provider" errors. If you experience
    this issue, please upgrade or consult `ticket #5360.
    <https://github.com/kivy/kivy/issues/5360>`_

Running the demo
----------------

Go to your `kivy/examples` folder, you'll have tons of demo you could try.

You could start the showcase::

    cd kivy/examples/demo/showcase
    python3 main.py

3d monkey demo is also fun too see::

    cd kivy/examples/3Drendering
    python3 main.py

Change the default screen to use
--------------------------------

You can set an environment variable named `KIVY_BCM_DISPMANX_ID` in order to
change the display used to run Kivy. For example, to force the display to be
HDMI, use::

    KIVY_BCM_DISPMANX_ID=2 python3 main.py

Check :ref:`environment` to see all the possible values.

Using Official RPi touch display
--------------------------------

If you are using the official Raspberry Pi touch display, you need to
configure Kivy to use it as an input source. To do this, edit the file
``~/.kivy/config.ini`` and go to the ``[input]`` section. Add this:

::

    mouse = mouse
    mtdev_%(name)s = probesysfs,provider=mtdev
    hid_%(name)s = probesysfs,provider=hidinput

For more information about configuring Kivy, see :ref:`configure kivy`

Where to go ?
-------------

We made few games using GPIO / physical input we got during Pycon 2013: a
button and a tilt. Checkout the https://github.com/kivy/piki. You will need to
adapt the GPIO pin in the code.

A video to see what we were doing with it:
http://www.youtube.com/watch?v=NVM09gaX6pQ
