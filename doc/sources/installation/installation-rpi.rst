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

Raspberry Pi OS Buster/Bullseye/Bookworm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using apt::

    sudo apt update
    sudo apt install python3 python3-pip

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

To install Kivy from source, please follow the :ref:`installation guide<kivy-wheel-install>` until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the dependencies below
before continuing.

Raspberry Pi OS Buster/Bullseye/Bookworm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using apt::

    sudo apt update
    apt-get -y install build-essential git make autoconf automake libtool \
          pkg-config cmake ninja-build libasound2-dev libpulse-dev libaudio-dev \
          libjack-dev libsndio-dev libsamplerate0-dev libx11-dev libxext-dev \
          libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libwayland-dev \
          libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev libgles2-mesa-dev \
          libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev libudev-dev fcitx-libs-dev

    apt-get install xorg wget libxrender-dev lsb-release libraspberrypi-dev raspberrypi-kernel-headers

    # If we're on Debian buster, we need to install cmake from backports as the cmake version
    # in buster is too old to build sdl2
    if [ "$(lsb_release -cs)" = "buster" ]; then \
        echo "deb http://deb.debian.org/debian buster-backports main" >> /etc/apt/sources.list; \
        apt-get update; \
        apt-get -y install -t buster-backports cmake; \
    fi

Cross-Compilation for Raspberry Pi OS Buster/Bullseye/Bookworm (32 bit)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Kivy performs a dockerized cross-compilation for Raspberry Pi OS Buster/Bullseye/Bookworm (32 bit) wheels.
The base images used for cross-compilation are the `balenalib`_ images for raspberrypi3 (buster, bullseye and bookworm).

.. _balenalib: https://www.balena.io/docs/reference/base-images/base-images-ref/

The docker images are built using the `Dockerfile.armv7l` file in the `.ci` directory.

The raspberrypi3 balenalib images have almost the same environment as the real Raspberry Pi OS Buster/Bullseye (32 bit) system,
which makes it possible to include/exclude RPi specific features (like the `egl_rpi` window provider) during the build process.

We have an helper, named `generate_rpi_wheels`, that can be used to easily generate the wheels and copy the artifacts for Raspberry Pi OS Buster/Bullseye (32 bit).
To cross-compile the wheels, you need to run the following commands::

    source .ci/ubuntu_ci.sh

    # Generate wheels for Raspberry Pi OS Buster (32 bit, Python 3.7)
    generate_rpi_wheels balenalib/raspberrypi3-debian-python:3.7-buster

    # Generate wheels for Raspberry Pi OS Bullseye (32 bit, Python 3.9)
    generate_rpi_wheels balenalib/raspberrypi3-debian-python:3.9-bullseye

    # Generate wheels for Raspberry Pi OS Bookworm (32 bit, Python 3.11)
    generate_rpi_wheels balenalib/raspberrypi3-debian-python:3.11-bookworm


Kivy determines automatically the sub-packages to build based on the environment it is compiled within. By default, the `egl_rpi` renderer that 
uses the (now deprecated but still useful) DISPMANX API is only compiled when running on a Raspberry Pi with Raspberry Pi OS Buster (32 bit), as it is the only
platform that still  supports it.

Please note that the `egl_rpi` window handler is not supported on Raspberry Pi 4 and higher.

Headless support on Raspberry Pi
--------------------------------

If you followed the previous steps, or you're using the pre-built wheels, the headless support is enabled by default.

On supported platforms (RPi 1-3 with Raspberry Pi OS Buster), the `egl_rpi` window provider is used by default. This window provider uses the
(deprecated, will be removed in future) DISPMANX API to create a headless GL context.

On other platforms (e.g RPi 4 or 64 bit OS), the `sdl2` window provider is used by default. If during the build process for the `sdl2` 
dependencies the `kmsdrm` headers and libraries are found, the `kmsdrm` backend is enabled. This backend allows to create a headless 
GL context using the KMS/DRM API.

Hardware acceleration
---------------------

If you are getting output similar to this when running your app::

    [INFO   ] GL: OpenGL vendor <b'VMware, Inc.'>
    [INFO   ] GL: OpenGL renderer <b'llvmpipe (LLVM 9.0.1, 128 bits)'>

Then it means that the renderer is **NOT** hardware accelerated. This can be fixed by adding your user to the render group::

    sudo adduser "$USER" render

You will then see an output similar to this::

    [INFO   ] GL: OpenGL vendor <b'Broadcom'>
    [INFO   ] GL: OpenGL renderer <b'V3D 4.2'>


Raspberry Pi window provider and GL backend
-------------------------------------------

Where applicable, Kivy will use the `egl_rpi` window provider by default.

The window provider and GL backend can be changed at runtime by setting the `KIVY_WINDOW`_ and `KIVY_GL_BACKEND`_ environmental variables.

The table below shows the supported combinations of window provider and GL backend on the 4 platforms:

+------------------------------------+-----------------------------------+-------+-------+-------+-------+
| Window provider (`KIVY_WINDOW`_\=) | GL backend (`KIVY_GL_BACKEND`_\=) | RPi 1 | RPi 2 | RPi 3 | RPi 4 |
+====================================+===================================+=======+=======+=======+=======+
| sdl2                               | sdl2/gl                           | y     | y     | y     | y     |
+------------------------------------+-----------------------------------+-------+-------+-------+-------+
| x11                                | gl                                | y     | y     | y     | y     |
+------------------------------------+-----------------------------------+-------+-------+-------+-------+
| egl_rpi                            | gl                                | y*    | y*    | y*    | n     |
+------------------------------------+-----------------------------------+-------+-------+-------+-------+

*The ``egl_rpi`` (deprecated) window provider is only available on Raspberry Pi OS Buster (32 bit).

.. _KIVY_WINDOW: https://kivy.org/doc/stable/guide/environment.html#restrict-core-to-specific-implementation
.. _KIVY_GL_BACKEND: https://kivy.org/doc/stable/guide/environment.html#restrict-core-to-specific-implementation

Change the default screen to use
--------------------------------

You can set an environment variable named `KIVY_BCM_DISPMANX_ID` in order to
change the display used to run Kivy. For example, to force the display to be
HDMI, use::

    KIVY_BCM_DISPMANX_ID=2 python3 main.py

Check :ref:`environment` to see all the possible values.

Note that this is only available on Raspberry Pi OS Buster (32 bit) and only when using the `egl_rpi` window provider.

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
