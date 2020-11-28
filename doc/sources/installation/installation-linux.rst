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

Python and python-pip must be installed from the package manager:

Ubuntu
~~~~~~

Using apt::

    sudo apt-get install -y \
        python3-pip \
        build-essential \
        git \
        python3 \
        python3-dev \

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

To install Kivy from source, please follow the installation guide until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the dependencies below
before continuing. Additionally, if you'd like to be able to use the x11 window backend do::

    export USE_X11=1

Ubuntu
~~~~~~

Using apt::

    # Install necessary system packages
    sudo apt-get install -y \
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


Fedora
~~~~~~

Using dnf::

    # Install necessary system packages
    sudo dnf install -y ffmpeg-libs SDL2-devel SDL2_image-devel SDL2_mixer-devel \
    SDL2_ttf-devel portmidi-devel libavdevice libavc1394-devel zlibrary-devel ccache \
    mesa-libGL mesa-libGL-devel
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

#. There is a kivy ebuild (kivy stable version)

   emerge Kivy

#. available USE-flags are:

   `cairo: Standard flag, let kivy use cairo graphical libraries.`
   `camera: Install libraries needed to support camera.`
   `doc: Standard flag, will make you build the documentation locally.`
   `examples: Standard flag, will give you kivy examples programs.`
   `garden: Install garden tool to manage user maintained widgets.`
   `gstreamer: Standard flag, kivy will be able to use audio/video streaming libraries.`
   `spell: Standard flag, provide enchant to use spelling in kivy apps.`


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
