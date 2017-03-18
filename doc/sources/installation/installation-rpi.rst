.. _installation_rpi:

Installation on Raspberry Pi
============================

You can install Kivy manually, or you can download and boot KivyPie on the
Raspberry Pi. Both options are described below.


Manual installation (On Raspbian Jessie)
----------------------------------------

#. Install the dependencies::

    sudo apt-get update
    sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
       pkg-config libgl1-mesa-dev libgles2-mesa-dev \
       python-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python-dev libmtdev-dev \
       xclip

#. Install a new enough version of Cython::

    sudo pip install -I Cython==0.23


#. Install Kivy globally on your system::

    sudo pip install git+https://github.com/kivy/kivy.git@master


#. Or build and use kivy inplace (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy
    
    make
    echo "export PYTHONPATH=$(pwd):\$PYTHONPATH" >> ~/.profile
    source ~/.profile
    

Manual installation (On Raspbian Wheezy)
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
       python-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python-dev

#. Install pip from source::

    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    sudo python get-pip.py

#. Install Cython from sources (debian package are outdated)::

    sudo pip install cython

#. Install Kivy globally on your system::

    sudo pip install git+https://github.com/kivy/kivy.git@master

#. Or build and use kivy inplace (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy
    
    make
    echo "export PYTHONPATH=$(pwd):\$PYTHONPATH" >> ~/.profile
    source ~/.profile


KivyPie distribution
--------------------

KivyPie is a compact and lightweight Raspbian based distribution that comes
with Kivy installed and ready to run. It is the result of applying the manual
installation steps described above, with a few more extra tools. You can
download the image from http://kivypie.mitako.eu/kivy-download.html and boot
it on a Raspberry PI.


Running the demo
----------------

Go to your `kivy/examples` folder, you'll have tons of demo you could try.

You could start the showcase::

    cd kivy/examples/demo/showcase
    python main.py

3d monkey demo is also fun too see::

    cd kivy/examples/3Drendering
    python main.py

Change the default screen to use
--------------------------------

You can set an environment variable named `KIVY_BCM_DISPMANX_ID` in order to
change the display used to run Kivy. For example, to force the display to be
HDMI, use::

    KIVY_BCM_DISPMANX_ID=2 python main.py

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
