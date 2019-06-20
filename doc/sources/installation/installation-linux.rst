.. _installation_linux:

Installation on Linux
=====================

Using Precompiled Wheels
------------------------

.. note::

    Linux wheels are new and still experimental, if you run into issues, uninstall
    it and use any of the other installation methods listed further down.

Wheels are precompiled binaries for all linux platforms using the manylinux2010 tag.
In the following, replace `python` with `python3` for Python 3.
To install first update pip::

    $ python -m pip install --upgrade --user pip setuptools virtualenv

Then make and load the virtualenv. This is optional, but highly recommended::

    $ python -m virtualenv ~/kivy_venv
    $ source ~/kivy_venv/bin/activate

Finally install the Kivy wheel and optionally the kivy-examples::

    $ python -m pip install kivy
    $ python -m pip install kivy_examples

Gstreamer is not included, so if you would like to use media playback with kivy,
you should install `ffpyplayer` like so ::

    $ python -m pip install ffpyplayer

Make sure to set `KIVY_VIDEO=ffpyplayer` env variable before running the app.
Only Python 3.5+ is supported.

Nightly wheel installation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. |cp35_linux| replace:: Python 3.5
.. _cp35_linux: https://kivy.org/downloads/ci/linux/kivy/Kivy-2.0.0.dev0-cp35-cp35m-manylinux2010_x86_64.whl
.. |cp36_linux| replace:: Python 3.6
.. _cp36_linux: https://kivy.org/downloads/ci/linux/kivy/Kivy-2.0.0.dev0-cp36-cp36m-manylinux2010_x86_64.whl
.. |cp37_linux| replace:: Python 3.7
.. _cp37_linux: https://kivy.org/downloads/ci/linux/kivy/Kivy-2.0.0.dev0-cp37-cp37m-manylinux2010_x86_64.whl
.. |examples_whl_linux| replace:: Kivy examples
.. _examples_whl_linux: https://kivy.org/downloads/appveyor/kivy/Kivy_examples-2.0.0.dev0-py2.py3-none-any.whl

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

Snapshot wheels of current Kivy master are created daily on the
`master` branch of kivy repository. They can be found
`here <https://kivy.org/downloads/ci/linux/kivy/>`_. To use them, instead of
doing ``python -m pip install kivy`` we'll install one of these wheels as
follows.

- |cp35_linux|_
- |cp36_linux|_
- |cp37_linux|_

#. Download the appropriate wheel for your Python version.
#. Install it as above but with ``pip install wheel-name`` where ``wheel-name``
   is the name of the file, instead.

Kivy examples are separated from the core because of their size. The examples
can be installed separately on all Python versions with this single wheel:

- |examples_whl_linux|_

Using Conda
-----------

If you use Anaconda, you can simply install kivy using::

   $ conda install kivy -c conda-forge

Using software packages (PPA etc.)
----------------------------------


Ubuntu / Kubuntu / Xubuntu / Lubuntu (Saucy and above)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Manually installing Kivy from source
------------------------------------

For other distros or to manually install Kivy from source, see :ref:`installation_in_venv`.
