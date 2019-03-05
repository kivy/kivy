.. _installation:

Basic Installation
==================

Kivy offers a lot of customizability when it comes to installation. The following lists an easy installation method for each platform that should bring
along all necessary dependencies. Ways to adjust how kivy is installed and how to setup kivy for developement can be read below under the :ref:`advanced_installation` section.

Note that Kivy runs on even more platforms than the ones listed below. See :ref:`packaging` for a list of all supported target platforms.

Windows
~~~~~~~

Install kivy along with Windows-specific dependencies::

    $ pip3 install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew kivy.deps.gstreamer kivy

Optionally, install examples featured in the `Gallery of Examples <https://kivy.org/doc/stable/examples/gallery.html>`_::

    $ pip3 install kivy_examples

OS X
~~~~

First, install necessary packages using homebrew::

    $ brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

Then install kivy using pip::

    $ pip install Cython==0.26.1 kivy

Optionally, install examples featured in the `Gallery of Examples <https://kivy.org/doc/stable/examples/gallery.html>`_::

    $ pip install kivy_examples


Linux
~~~~~

Ubuntu based Distros (Ubuntu, Mint, Bhodi)    
++++++++++++++++++++++++++++++++++++++++++

Add kivy PPA::

    $ sudo add-apt-repository ppa:kivy-team/kivy

Update packages list of apt::

    $ sudo apt update

Install kivy dependencies (leave out the `3` for Python 2.x)::

    $ sudo apt-get install python3-kivy

Optionally, install some examples featured in the `Gallery of Examples <https://kivy.org/doc/stable/examples/gallery.html>`_::

    $ sudo apt install kivy-examples


Debian (Jessie or newer)
++++++++++++++++++++++++

Add kivy PPA::

    $ deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu xenial main

Add GPG to your apt keyring for our repository::

    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6

Update package list of apt::

    $ sudo apt update

Install kivy dependencies (leave out the `3` for Python 2.x)::

    $ sudo apt-get install python3-kivy

Optionally, install some examples featured in the `Gallery of Examples <https://kivy.org/doc/stable/examples/gallery.html>`_::

    $ sudo apt install kivy-examples

Raspberri Pi
++++++++++++

Installation on a Raspberri Pi is a little complicated, its instructions can be found on a separate page: :ref:`installation_rpi`.


Other Distros
+++++++++++++

For other distros, we recommend :ref:`installation_in_venv` .

.. _advanced_installation:

Advanced Installation
=====================

In trying to avoid reinenting the wheel, we try to use as many third-party packages as possible.
Not all of them necessarily have to be installed if only a subset of kivy's features are desired. 
Additionally, some dependencies may be swapped with others if your platform doesn't support one of them.
Finally, for some platforms, there are multiple ways to installing certain dependencies. If you prefer a different
method than the one listed above, the following guides might also be of interest for you.

Stable Builds
~~~~~~~~~~~~~

Methods with fine-grained control over kivy's installation can be found under the following links:

.. toctree::
    :maxdepth: 1

    installation-windows
    installation-osx
    installation-linux
    installation-android
    installation-rpi

Development Version
~~~~~~~~~~~~~~~~~~~

The development version is for developers and testers. Note that when
running a development version, you're running potentially broken code at
your own risk. 

If that is something of interest to you, read more here:

.. might later be replaced with a toc listing different platforms, like under Stable Builds

-  :ref:`installation_devel`
- `Contributing Guidelines <contributing>`_


Uninstalling Kivy
=================

If you are mixing multiple Kivy installations, you might be confused about where each Kivy version is
located. Please note that you might need to follow these steps multiple times if you have multiple
Kivy versions installed in the Python library path.
To find your current installed version, you can use the command line::

    $ python -c 'import kivy; print(kivy.__path__)'

Then, remove that directory recursively.

If you have installed Kivy with easy_install on linux, the directory may
contain a "egg" directory. Remove that as well::

    $ python -c 'import kivy; print(kivy.__path__)'
    ['/usr/local/lib/python2.7/dist-packages/Kivy-1.0.7-py2.7-linux-x86_64.egg/kivy']
    $ sudo rm -rf /usr/local/lib/python2.7/dist-packages/Kivy-1.0.7-py2.7-linux-x86_64.egg

If you have installed with apt-get, do::

    $ sudo apt-get remove --purge python-kivy
