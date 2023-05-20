.. _installation_linux:

Installation on Linux
=====================

To install Kivy on Linux using ``pip``, please follow the main :ref:`installation guide<installation-canonical>`.
Otherwise, continue to the :ref:`PPA instructions below<linux-ppa>`.

Installation components
-----------------------

Following, are additional information linked to from some of the steps in the
main :ref:`pip installation guide<installation-canonical>`, specific to Linux.

.. _install-python-linux:

Installing Python
^^^^^^^^^^^^^^^^^

Python and pip are already installed on most Linux distributions. If you don't have Python installed, you can
install it using your distribution's package manager.

Ubuntu
~~~~~~

Using apt::

    sudo apt-get update

    sudo apt-get install -y \
        python3-pip \
        python3

Fedora
~~~~~~

You will likely need to do this preliminary step which installs the rpmfusion-free repository unless you have some
other 3rd-party repo installed which has the required packages. See rpmfusion.org for complete installation
instructions, but only the rpmfusion-free repo is needed for acquiring kivy dependencies
(though rpmfusion-nonfree is recommended by rpm fusion installation instructions) as shown in this step.

Using dnf::

    sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm

After you ensure that a 3rd-party repository containing any packages that dnf is otherwise unable to find,
continue installing dependencies::

    sudo dnf install -y python3-devel

.. _install-source-linux:

Source installation Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Kivy from source, please follow the :ref:`installation guide<kivy-wheel-install>` until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the dependencies below
before continuing. Additionally, if you'd like to be able to use the x11 window backend do::

   export USE_X11=1

Ubuntu
~~~~~~

Using apt::

    sudo apt-get update

    # Install build tools, and dependencies to perform a full build (including SDL2 dependencies)
    sudo apt-get -y install python3-dev build-essential git make autoconf automake libtool \
          pkg-config cmake ninja-build libasound2-dev libpulse-dev libaudio-dev \
          libjack-dev libsndio-dev libsamplerate0-dev libx11-dev libxext-dev \
          libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libwayland-dev \
          libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev libgles2-mesa-dev \
          libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev libudev-dev fcitx-libs-dev


Fedora
~~~~~~

Using dnf::

    sudo dnf install epel-release

    # Install build tools, and dependencies to perform a full build (including SDL2 dependencies)
    yum -y install autoconf automake cmake gcc gcc-c++ git make pkgconfig \
            ninja-build alsa-lib-devel pulseaudio-libs-devel \
            libX11-devel libXext-devel libXrandr-devel libXcursor-devel libXfixes-devel \
            libXi-devel libXScrnSaver-devel dbus-devel ibus-devel fcitx-devel \
            systemd-devel mesa-libGL-devel libxkbcommon-devel mesa-libGLES-devel \
            mesa-libEGL-devel wayland-devel wayland-protocols-devel \
            libdrm-devel mesa-libgbm-devel libsamplerate-devel

    # Install xclip in case you run a kivy app using your computer, and the app requires a CutBuffer provider:
    sudo dnf install -y xclip

    #
    # In case you get the following error preventing kivy install:
    #  annobin: _event.c: Error: plugin built for compiler version (8.0.1) but run with compiler version (8.1.1)
    #  cc1: error: fail to initialize plugin /usr/lib/gcc/86_64-redhat-linux/8/plugin/annobin.so
    # This has been resolved in later updates after the on-disk release of Fedora 28, so upgrade your packages:
    #  sudo dnf -y upgrade

.. _linux-ppa:

Using software packages (PPA etc.)
----------------------------------

Ubuntu / Kubuntu / Xubuntu / Lubuntu (Saucy and above)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Add one of the PPAs as you prefer

    :stable builds:
        $ sudo add-apt-repository ppa:kivy-team/kivy
    :nightly builds:
        $ sudo add-apt-repository ppa:kivy-team/kivy-daily

#. Update your package list using your package manager
    $ sudo apt-get update

#. Install Kivy

    :Python3 - **python3-kivy**:
        $ sudo apt-get install python3-kivy
    :optionally the `gallery of Examples <../examples/gallery.html>`_ - **kivy-examples**:
        $ sudo apt-get install kivy-examples


Debian  (Jessie or newer)
~~~~~~~~~~~~~~~~~~~~~~~~~

#. Add one of the PPAs to your sources.list in apt manually or via Synaptic

    :stable builds:
        deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu xenial main
    :daily builds:
        deb http://ppa.launchpad.net/kivy-team/kivy-daily/ubuntu xenial main

    **Notice**: Wheezy is not supported - You'll need to upgrade to Jessie at least!

#. Add the GPG key to your apt keyring by executing

    as user:

    ``sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6``

    as root:

    ``apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6``

#. Refresh your package list and install **python-kivy** and/or **python3-kivy** and optionally the examples
   found in **kivy-examples**


Linux Mint
~~~~~~~~~~

#. Find out on which Ubuntu release your installation is based on, using this
   `overview <https://linuxmint.com/download_all.php>`_.
#. Continue as described for Ubuntu above, depending on which version your
   installation is based on.


Bodhi Linux
~~~~~~~~~~~

#. Find out which version of the distribution you are running and use the table below
   to find out on which Ubuntu LTS it is based.

    :Bodhi 1:
        Ubuntu 10.04 LTS aka Lucid (No packages, just manual install)
    :Bodhi 2:
        Ubuntu 12.04 LTS aka Precise
    :Bodhi 3:
        Ubuntu 14.04 LTS aka Trusty
    :Bodhi 4:
        Ubuntu 16.04 LTS aka Xenial


2. Continue as described for Ubuntu above, depending on which version your installation is based on.


OpenSuSE
~~~~~~~~

#. To install kivy go to http://software.opensuse.org/package/python-Kivy and use the "1 Click Install" for your openSuse version. You might need to make the latest kivy version appear in the list by clicking on "Show unstable packages". We prefer to use packages by " devel:languages:python".

#. If you would like access to the examples, please select **python-Kivy-examples** in the upcoming installation wizard.


Gentoo
~~~~~~

#. **Add** the `raiagent overlay <https://github.com/leycec/raiagent>`_
   packaging the `full Kivy + KivyMD + Buildozer + python-for-android stack
   <https://github.com/kivy/kivy/issues/7868>`_.

   .. code-block:: bash

      eselect repository enable raiagent

#. **Synchronize** (i.e., fetch) this overlay.

   .. code-block:: bash

      emerge --sync raiagent

#. Install **Kivy** and optionally **KivyMD**, **Buildozer**, and
   **python-for-android**.

   .. code-block:: bash

      emerge --ask --autounmask Kivy kivymd buildozer python-for-android

#. (\ *Optional*\ ) Describe all **USE flags** supported by these ebuilds.

   .. code-block:: bash

      equery u Kivy kivymd buildozer python-for-android


Device permissions
------------------

When you app starts, Kivy uses `Mtdev <http://wiki.ubuntu.com/Multitouch>`_ to
scan for available multi-touch devices to use for input. Access to these
devices is typically restricted to users or groups with the appropriate
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
