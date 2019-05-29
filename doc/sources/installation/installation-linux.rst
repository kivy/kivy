.. _installation_linux:

Installation on Linux
=====================

Using Wheels
------------

Wheels are precompiled binaries for all linux platforms using the manylinux2010 tag.
All you need to do to install kivy using wheels on linux is ::

    $ python -m pip install kivy

Gstreamer is not included, so if you would like to use media playback with kivy,
you should install `ffpyplayer` like so ::

    $ python -m pip install ffpyplayer

Make sure to set `KIVY_VIDEO=ffpyplayer` env variable before running the app.
Only Python 3.5+ is supported.

Using software packages
~~~~~~~~~~~~~~~~~~~~~~~

For installing distribution relative packages .deb/.rpm/...


Ubuntu / Kubuntu / Xubuntu / Lubuntu (Saucy and above)
------------------------------------------------------

#. Add one of the PPAs as you prefer

    :stable builds:
        $ sudo add-apt-repository ppa:kivy-team/kivy
    :nightly builds:
        $ sudo add-apt-repository ppa:kivy-team/kivy-daily

#. Update your package list using your package manager
    $ sudo apt-get update

#. Install Kivy

    :Python2 - **python-kivy**:
        $ sudo apt-get install python-kivy
    :Python3 - **python3-kivy**:
        $ sudo apt-get install python3-kivy
    :optionally the `gallery of Examples <../examples/gallery.html>`_ - **kivy-examples**:
        $ sudo apt-get install kivy-examples


Debian  (Jessie or newer)
-------------------------

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
----------

#. Find out on which Ubuntu release your installation is based on, using this
   `overview <https://linuxmint.com/download_all.php>`_.
#. Continue as described for Ubuntu above, depending on which version your
   installation is based on.


Bodhi Linux
-----------

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
--------

#. To install kivy go to http://software.opensuse.org/package/python-Kivy and use the "1 Click Install" for your openSuse version. You might need to make the latest kivy version appear in the list by clicking on "Show unstable packages". We prefer to use packages by " devel:languages:python".

#. If you would like access to the examples, please select **python-Kivy-examples** in the upcoming installation wizard.


Gentoo
------

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

Other
-----

For other distros, we recommend :ref:`installation_in_venv`.
