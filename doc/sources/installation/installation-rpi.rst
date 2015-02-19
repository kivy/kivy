.. _installation_rpi:

Installation on Raspberry Pi
============================

Currently you can install Kivy manually, or you can download and boot KivyPie on the RaspberryPI. Both options are described below.

KivyPie distribution
--------------------

KivyPie is a free Raspbian based distribution that comes with Kivy installed and ready to run.
It is the result of applying the manual installation steps described below, with a few more extra tools.

There are no X libraries or X Server installed, that means it is compact and lightweight.
You can download the image from http://kivypie.mitako.eu/kivy-download.html and boot it on the RaspberryPI.

It supports popular keyboards, mice, and it is reported to play well with the PiTouch screen.
If you are experiencing problems with other devices you should tweak the file `~/.kivy/config.ini`,
the options available are documented here: http://kivy.org/docs/api-kivy.config.html#module-kivy.config

KivyPie also comes with a screenshot tool that allows for taking still pictures from your games & designs.

For download and more inside details visit the KivyPie project: http://kivypie.mitako.eu/


Manual installation
-------------------

#. Add APT sources for Gstreamer 1.0 in `/etc/apt/sources.list`::

    deb http://vontaene.de/raspbian-updates/ . main
    
#. Install the dependencies::

    sudo apt-get update
    sudo apt-get install pkg-config libgl1-mesa-dev libgles2-mesa-dev \
       python-pygame python-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python-dev

#. Install pip from source::

    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    sudo python get-pip.py

#. Install Cython from sources (debian package are outdated)::

    sudo pip install cython

#. Clone and compile Kivy::

    git clone https://github.com/kivy/kivy
    cd kivy

#. Build and use kivy inplace (best for development)::

    make
    echo "export PYTHONPATH=$(pwd):\$PYTHONPATH" >> ~/.profile
    source ~/.profile

#. Or install Kivy globally on your system::

    python setup.py build
    sudo python setup.py install


Running the demo
----------------

Go to your `kivy/examples` folder, you'll have tons of demo you could try.

You could start the showcase::

    cd kivy/examples/demo/showcase
    python main.py

3d monkey demo is also fun too see::

    cd kivy/examples/3Drendering
    python main.py


Where to go ?
-------------

We made few games using GPIO / physical input we got during Pycon 2013: a
button and a tilt. Checkout the https://github.com/kivy/piki. You will need to
adapt the GPIO pin in the code.

A video to see what we were doing with it:
http://www.youtube.com/watch?v=NVM09gaX6pQ

A handful of examples are also available on the KivyPie distribution to get you started:
http://kivypie.mitako.eu/kivy-gallery.html
