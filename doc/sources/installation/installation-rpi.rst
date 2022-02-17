.. _installation_rpi:

Installation on Raspberry Pi
============================

To install Kivy on the RPi using ``pip``, please follow the main :ref:`installation guide<installation-canonical>`.

Installation components
-----------------------

Following, are additional information linked to from some of the steps in the
main :ref:`pip installation guide<installation-canonical>`, specific to the RPi.

.. _install-python-rpi:

Installing Python
^^^^^^^^^^^^^^^^^

Python and python-pip must be installed from the package manager:

Raspbian Jessie/Stretch/Buster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using apt::

    sudo apt update
    sudo apt install python3-setuptools git-core python3-dev

Arch Linux ARM
~~~~~~~~~~~~~~

Images to use::

    http://raspex.exton.se/?p=859 (recommended)
    https://archlinuxarm.org/

Using pacman::

    sudo pacman -Syu
    # Note: python-setuptools needs to be installed through pacman or it will result with conflicts!
    sudo pacman -S python-setuptools

    # Install pip from source
    wget https://bootstrap.pypa.io/get-pip.py
    # or curl -O https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py

.. _install-source-rpi:

Source installation Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Kivy from source, please follow the installation guide until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the dependencies below
before continuing.

Raspbian Jessie/Stretch/Buster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using apt::

    sudo apt update
    sudo apt install pkg-config libgl1-mesa-dev libgles2-mesa-dev \
       libgstreamer1.0-dev \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} libmtdev-dev \
       xclip xsel libjpeg-dev

And then install SDL2 using either of the two options below depending on whether you
will be running Kivy from a headless or desktop environment:

Raspberry Pi 1-4 Desktop environment
************************************

If you have installed Raspbian with a desktop i.e. if your Raspberry Pi boots into a desktop environment
then install SDL2 from apt::

    sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

Cross-Compilation for Raspberry Pi 1-3 headless installation on Raspbian Buster
*******************************************************************************

The Raspberry OS project uses `pi-gen` project to create bootable images for Raspberry PI.

Kivy determines automatically the sub-packages to build based on the environment it is compiled within. By default, the `egl_rpi` renderer that uses the (now deprecated but still useful) DISPMANX API is only compiled when running on a Raspberry Pi.
In order to build Kivy in such `pi-gen` environment, the auto-detection of the Raspberry Pi hardware version needs to be disabled.

When cross-compiling using e.g. `pi-gen`, the build system can be forced into compiling for Raspberry Pi with `egl_rpi` support by setting the environment variabel `KIVY_RPI_VERSION` to any number < 4, e.g. `3`.

The install command then looks something like this::

    apt install build-essential libraspberrypi-dev raspberrypi-kernel-headers
    KIVY_RPI_VERSION=3 python -m pip install "kivy[base]" kivy_examples --no-binary kivy

Please note that the `egl_rpi` window handler is not supported on Raspberry Pi 4 and higher.
The existing version check will refuse to compile the `egl_rpi` provider when detecting or forcing the Raspberry Pi version to 4 or higher.

Raspberry Pi 4 headless installation on Raspbian Buster
*******************************************************

If you run Kivy from the console and not from a desktop environment, you need to compile SDL2
from source, as the one bundled with Buster is not compiled with the ``kmsdrm`` backend,
so it only works under ``X11``.

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

If you are getting output similar to this when running your app::

    [INFO   ] GL: OpenGL vendor <b'VMware, Inc.'>
    [INFO   ] GL: OpenGL renderer <b'llvmpipe (LLVM 9.0.1, 128 bits)'>

Then it means that the renderer is **NOT** hardware accelerated. This can be fixed by adding your user to the render group::

    sudo adduser "$USER" render

You will then see an output similar to this::

    [INFO   ] GL: OpenGL vendor <b'Broadcom'>
    [INFO   ] GL: OpenGL renderer <b'V3D 4.2'>


Arch Linux ARM
~~~~~~~~~~~~~~

Using pacman::

    sudo pacman -S sdl2 sdl2_gfx sdl2_image sdl2_net sdl2_ttf sdl2_mixer

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
