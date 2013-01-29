.. _installation_linux:

Installation on Linux
=====================

Using software packages
~~~~~~~~~~~~~~~~~~~~~~~

Ubuntu
------

#. Add one of the PPAs as you prefer

:stable builds:
    $ sudo add-apt-repository ppa:kivy-team/kivy
:nightly builds:
    $ sudo add-apt-repository ppa:kivy-team/kivy-daily

2. Update your packagelist with your package manager
#. Install **python-kivy** and optionally the examples, found in **python-kivy-examples**

Debian
------

#. Add one of the PPAs into your sources.list in apt manually or via Synaptic

* Wheezy:
:stable builds:
    deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu oneiric main
:nightly builds:
    deb http://ppa.launchpad.net/kivy-team/kivy-daily/ubuntu oneiric main

* Sqeeze:
:stable builds:
    deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu lucid main
:nightly builds:
    deb http://ppa.launchpad.net/kivy-team/kivy-daily/ubuntu lucid main

2. Add the GPG key to your apt keyring by

:generally:
    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6

3. Refresh your package list and install **python-kivy** and optionally the examples as found in **python-kivy-examples**

OpenSuSE
--------

#. Installing via One-Click-Install

:Factory:
    `One-Click-Install <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_Factory/python-Kivy.ymp?base=openSUSE%3AFactory&query=python-Kivy>`_
:12.2:
    `One-Click-Install <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_12.2/python-Kivy.ymp?base=openSUSE%3A12.2&query=python-Kivy>`_
:12.1:
    `One-Click-Install <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_12.1/python-Kivy.ymp?base=openSUSE%3A12.1&query=python-Kivy>`_
:Tumbleweed:
    `One-Click-Install <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_Tumbleweed/python-Kivy.ymp?base=openSUSE%3A12.2&query=python-Kivy>`_

2. Use your preferred package-manager to install the examples, as found in **python-Kivy-examples**

Fedora
------

#. Adding the repository via terminal:

:Fedora 17:
    $ sudo yum-config-manager --add-repo=http://download.opensuse.org/repositories/home:/thopiekar:/kivy/Fedora_17/home:thopiekar:kivy.repo
    
:Fedora 16:
    $ sudo yum-config-manager --add-repo=http://download.opensuse.org/repositories/home:/thopiekar:/kivy/Fedora_16/home:thopiekar:kivy.repo
    
2. Use now your preferred package-manager to refresh your packagelists
#. Install **python-Kivy** and the examples, as found in **python-Kivy-examples**


Using software bundles ( also known as tarballs )
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Providing dependencies*
------------------------

========================

General
-------
The following software is needed, even if your distribution is not listed above:

- `Python >= 2.6 and Python < 3 <http://www.python.org/>`_
- `PyGame <http://www.pygame.org/>`_
- `PyEnchant <http://packages.python.org/pyenchant/>`_
- `gst-python <http://gstreamer.freedesktop.org/modules/gst-python.html>`_
- `Cython >= 0.15 <http://cython.org/>`_

We prefer to use a package-manager to provide these dependencies.

Ubuntu
------
::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev cython


*Upgrade Cython ( <= Oneiric [11.10] )*

:Using our PPA:
    $ sudo add-apt-repository ppa:kivy-team/kivy-daily
    
    $ sudo apt-get update
    
    $ sudo apt-get install cython


:Using PIP:
    $ sudo apt-get install python-pip
    
    $ sudo pip install --upgrade cython

Fedora
------

::

    $ sudo yum install python-distutils-extra python-enchant freeglut PyOpenGL \
    SDL_ttf-devel SDL_mixer-devel pygame pygame-devel khrplatform-devel \
    mesa-libGLES mesa-libGLES-devel gstreamer-plugins-good gstreamer \
    gstreamer-python mtdev-devel python-pip
    $ sudo pip install --upgrade cython
    $ sudo pip instll pygments

OpenSuse
--------

::

    $ sudo zypper install python-distutils-extra python-pygame python-opengl \
    python-gstreamer-0_10 python-enchant gstreamer-0_10-plugins-good \
    python-devel Mesa-devel python-pip
    $ zypper install -t pattern devel_C_C++
    $ sudo pip install --upgrade cython
    $ sudo pip install pygments


Mageia 1 onwards
----------------

::

    $ su
    $ urpmi python-setuptools python-pygame python-opengl \
    gstreamer0.10-python python-enchant gstreamer0.10-plugins-good \
    python-cython lib64python-devel lib64mesagl1-devel lib64mesaegl1-devel \
    lib64mesaglesv2_2-devel make gcc
    $ easy_install pip
    $ pip install --upgrade cython
    $ pip install pygments

*Installation*
--------------

==============

If you're installing Kivy for the first time, do::

    $ sudo easy_install kivy

If you already installed kivy before, you can upgrade it with::

    $ sudo easy_install --upgrade kivy


.. _linux-run-app:


*Start from Command Line*
~~~~~~~~~~~~~~~~~~~~~~~~~

We are shipping some examples ready-to-run. However, theses examples are packaged inside the package. That's mean, you must known first where easy_install have installed your current kivy package, and go to the example directory::

    $ python -c "import pkg_resources; print pkg_resources.resource_filename('kivy', '../share/kivy-examples')"

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

If you don't know about Unix and symbolic link, you can create a link directly in your home directory, for an easier access. For example:

#. Get the example path from the command line above
#. Paste in your console::

    $ ln -s <path to kivy-examples> ~/

#. Then, you can access to kivy-examples directly in your Home directory::

    $ cd ~/kivy-examples
