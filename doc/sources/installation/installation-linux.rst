.. _installation_linux:

Installation on Linux
=====================

Using software packages
~~~~~~~~~~~~~~~~~~~~~~~

For installing distribution relative packages .deb/.rpm/...

Ubuntu / Kubuntu / Xubuntu / Lubuntu (Oneiric and above)
--------------------------------------------------------

#. Add one of the PPAs as you prefer

    :stable builds:
        $ sudo add-apt-repository ppa:kivy-team/kivy
    :nightly builds:
        $ sudo add-apt-repository ppa:kivy-team/kivy-daily

    **Notice for Lucid users**: Support has been dropped in stable PPA
    as Python 2.7 is required and only 2.6 is available. You can find
    Python 2.7 in the daily PPA, but manual installation is needed.
    
    **Notice for Oneiric users**: Oneiric is supported but uses Python2.6
    as the default interpreter. Don't forget to set python2.7 as the
    interpreter for your project. "python", which is linked to "python2.6",
    won't work.

#. Update your packagelist using your package manager
#. Install **python-kivy** and optionally the examples, found in **python-kivy-examples**

Debian
------

#. Add one of the PPAs to your sources.list in apt manually or via Synaptic

    * Wheezy:
        
        :stable builds:
            deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu oneiric main
        :daily builds:
            deb http://ppa.launchpad.net/kivy-team/kivy-daily/ubuntu oneiric main

        **Notice**: Don't forget to use the python2.7 interpreter
            

    * Sqeeze: 

        Update to Wheezy or install Kivy 1.5.1 from stable PPA:

        :stable builds:
            deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu oneiric main

#. Add the GPG key to your apt keyring by

    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6

#. Refresh your package list and install **python-kivy** and optionally the examples
   found in **python-kivy-examples**

Linux Mint
----------

#. Find out on which Ubuntu release your installation is based on, using this
   `overview <http://www.linuxmint.com/oldreleases.php>`_.
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

2. Continue as described for Ubuntu above, depending on which version your installation is based on.

OpenSuSE
--------

#. Installing via One-Click-Install
    
    
    #. `OpenSuSE Factory <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_Factory/python-Kivy.ymp?base=openSUSE%3AFactory&query=python-Kivy>`_
    #. `OpenSuSE 12.2 <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_12.2/python-Kivy.ymp?base=openSUSE%3A12.2&query=python-Kivy>`_
    #. `OpenSuSE 12.1 <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_12.1/python-Kivy.ymp?base=openSUSE%3A12.1&query=python-Kivy>`_
    #. `OpenSuSE Tumbleweed <http://software.opensuse.org/ymp/home:thopiekar:kivy/openSUSE_Tumbleweed/python-Kivy.ymp?base=openSUSE%3A12.2&query=python-Kivy>`_

2. If you would like access to the examples, use your preferred package-manager to install
   **python-Kivy-examples**

Fedora
------

#. Adding the repository via the terminal:

    **Fedora 18** ::
    
        $ sudo yum-config-manager --add-repo=http://download.opensuse.org/repositories/home:/thopiekar:/kivy/Fedora_18/home:thopiekar:kivy.repo
    
    **Fedora 17** ::
    
        $ sudo yum-config-manager --add-repo=http://download.opensuse.org/repositories/home:/thopiekar:/kivy/Fedora_17/home:thopiekar:kivy.repo
    
    **Fedora 16** ::
    
        $ sudo yum-config-manager --add-repo=http://download.opensuse.org/repositories/home:/thopiekar:/kivy/Fedora_16/home:thopiekar:kivy.repo
    

#. Use your preferred package-manager to refresh your packagelists

#. Install **python-Kivy** and optionally the examples, as found in **python-Kivy-examples**


Using software bundles ( also known as tarballs )
=================================================

*Providing dependencies*
~~~~~~~~~~~~~~~~~~~~~~~~

General
-------
The following software is needed, even if your distribution is not listed above:

- `Python >= 2.7 and Python < 3 <http://www.python.org/>`_
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

:Using our PPA: ::

    $ sudo add-apt-repository ppa:kivy-team/kivy-daily
    $ sudo apt-get update
    $ sudo apt-get install cython

.. ``

:Using PIP: ::

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
    $ sudo pip install pygments

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
    # urpmi python-setuptools python-pygame python-opengl \
    gstreamer0.10-python python-enchant gstreamer0.10-plugins-good \
    python-cython lib64python-devel lib64mesagl1-devel lib64mesaegl1-devel \
    lib64mesaglesv2_2-devel make gcc
    # easy_install pip
    # pip install --upgrade cython
    # pip install pygments

*Installation*
==============



If you're installing Kivy for the first time, do::

    $ sudo easy_install kivy

If you already installed kivy before, you can upgrade it with::

    $ sudo easy_install --upgrade kivy


.. _linux-run-app:


*Start from the Command Line*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We ship some examples that are ready-to-run. However, theses examples are packaged inside the package.
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

