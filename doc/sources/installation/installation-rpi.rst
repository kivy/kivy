.. _installation_rpi:

Installation on Raspberry Pi
============================

Raspberry Pi 4 headless installation on Raspbian Buster
------------------------------------------------

#. If you have installed Raspbian with a desktop i.e. if you Raspberry Pi boot into a desktop environment, then you can skip to `Raspberry Pi 1-4 installation`_.

   If you are using Raspbian Lite, then you first need to install X::

    sudo apt-get install xserver-xorg

#. Next install nodm from source, so it includes the following fix: `spanezz/nodm#1 <https://github.com/spanezz/nodm/pull/10>`_::

    sudo apt-get install libpam0g-dev help2man libx11-dev debhelper
    git clone https://github.com/slashblog/nodm.git
    pushd nodm
        git checkout d48a8f6266d3f464138e0e95b65896917c35c89f
        wget http://deb.debian.org/debian/pool/main/n/nodm/nodm_0.13-5.debian.tar.xz
        tar xf nodm_0.13-5.debian.tar.xz
        sudo dpkg-buildpackage -us -uc -b
    popd
    sudo dpkg -i nodm_0.13-*_armhf.deb
    sudo rm -rf nodm*

#. Now enable graphical login::

    sudo systemctl set-default graphical.target

#. Create a small test app::

    cat <<EOF > ~/app.py
    from kivy.app import App
    from kivy.uix.button import Button


    class TestApp(App):

        def build(self):
            return Button(text='hello world')


    if __name__ == '__main__':
        TestApp().run()
    EOF

#. It is recommend to use the the logger functionality instead of print statements: `<https://kivy.org/doc/stable/api-kivy.logger.html>`_, so they show up in the log.

   A small script can then be used to follow the latest log and restart the application by using the ``--restart`` argument::

    #!/bin/bash -e

    if [[ $* == *--restart* ]]; then
        sudo service nodm restart
        inotifywait -q ~/.kivy/logs -e create --format %w%f | xargs tail -f
    else
        ls -t -d ~/.kivy/logs/* | head -n1 | xargs tail -f
    fi

   Note that you need to install `inotify-tools` in order to use the restart functionality.

#. Configure nodm and start your app at boot::

    # Has the same effect as calling 'sudo dpkg-reconfigure nodm'
    sudo sh -c 'echo "NODM_ENABLED=true" > /etc/default/nodm'
    sudo sh -c 'echo "NODM_USER=$SUDO_USER" >> /etc/default/nodm' # Note that the variable SUDO_USER is used
    sudo sh -c 'echo "NODM_FIRST_VT='\''7'\''" >> /etc/default/nodm'
    sudo sh -c 'echo "NODM_XSESSION=/etc/X11/Xsession" >> /etc/default/nodm'
    sudo sh -c 'echo "NODM_X_OPTIONS='\''-nolisten tcp'\''" >> /etc/default/nodm'
    sudo sh -c 'echo "NODM_MIN_SESSION_TIME=60" >> /etc/default/nodm'
    sudo sh -c 'echo "NODM_X_TIMEOUT=300" >> /etc/default/nodm'

    # Start the app using nodm
    echo '#!/bin/bash' > ~/.xsession
    echo 'export DISPLAY=:0.0' >> ~/.xsession
    echo "python3 ~/app.py" >> ~/.xsession

#. Now simply follow the `Raspberry Pi 1-4 installation`_ instructions to install Kivy.

_`Raspberry Pi 1-4 installation` on Raspbian Jessie/Stretch/Buster
------------------------------------------------

#. Install the dependencies::

    sudo apt update
    sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
       pkg-config libgl1-mesa-dev libgles2-mesa-dev \
       python3-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python3-dev libmtdev-dev \
       xclip xsel libjpeg-dev

#. Install pip dependencies:

   .. parsed-literal::

    python3 -m pip install --upgrade --user pip setuptools
    python3 -m pip install --upgrade --user |cython_install| pillow

#. Install Kivy to Python globally

   You can install it like a normal python package with::

    # to get the last release from pypi
    python3 -m pip install --user kivy

    # to install master
    python3 -m pip install --user https://github.com/kivy/kivy/archive/master.zip

    # or clone locally then pip install
    git clone https://github.com/kivy/kivy
    cd kivy
    python3 -m pip install --user .

   Or build and use kivy inplace in a editable install (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy

    python3 -m pip install --user -e .
    # every time you change any cython files remember to manually call:
    make
    # or to recompile all files
    make force

   Or on a Raspberry Pi 4 it is possible to use a precompiled wheel. The precompiled wheel can be downloaded from the latest `release <https://github.com/kivy/kivy/releases>`_. A wheel is also automatically build daily and can be downloaded here: `<https://kivy.org/downloads/ci/raspberrypi/kivy>`_.

   The wheel can be installed as follows::

    python3 -m pip install --upgrade --user wheel
    python3 -m pip install --user *armv7l.whl

.. note::

    On versions of kivy prior to 1.10.1, Mesa library naming changes can result
    in "Unable to find any valuable Window provider" errors. If you experience
    this issue, please upgrade or consult `ticket #5360.
    <https://github.com/kivy/kivy/issues/5360>`_

Installation on Raspbian Wheezy
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
       python3-setuptools libgstreamer1.0-dev git-core \
       gstreamer1.0-plugins-{bad,base,good,ugly} \
       gstreamer1.0-{omx,alsa} python3-dev

#. Install pip from source::

    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    sudo python3 get-pip.py

#. Install Cython from sources (debian packages are outdated):

   .. parsed-literal::

    sudo pip install |cython_install|

#. Install Kivy globally on your system::

    sudo pip install git+https://github.com/kivy/kivy.git@master

#. Or build and use kivy inplace (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy

    make
    echo "export PYTHONPATH=$(pwd):\$PYTHONPATH" >> ~/.profile
    source ~/.profile

Installation on Arch Linux ARM
------------------------------------------------

#. Install the dependencies::

    sudo pacman -Syu
    sudo pacman -S sdl2 sdl2_gfx sdl2_image sdl2_net sdl2_ttf sdl2_mixer python-setuptools

    Note: python-setuptools needs to be installed through pacman or it will result with conflicts!

#. Install pip from source::

    wget https://bootstrap.pypa.io/get-pip.py
    or curl -O https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py

#. Install a new enough version of Cython:

   .. parsed-literal::

    sudo pip install -U |cython_install|

#. Install Kivy globally on your system::

    sudo pip install git+https://github.com/kivy/kivy.git@master

#. Or build and use kivy inplace (best for development)::

    git clone https://github.com/kivy/kivy
    cd kivy
    python setup.py install

Images to use::

    http://raspex.exton.se/?p=859 (recommended)
    https://archlinuxarm.org/

.. note::

    On versions of kivy prior to 1.10.1, Mesa library naming changes can result
    in "Unable to find any valuable Window provider" errors. If you experience
    this issue, please upgrade or consult `ticket #5360.
    <https://github.com/kivy/kivy/issues/5360>`_

Running the demo
----------------

Go to your `kivy/examples` folder, you'll have tons of demo you could try.

You could start the showcase::

    cd kivy/examples/demo/showcase
    python3 main.py

3d monkey demo is also fun too see::

    cd kivy/examples/3Drendering
    python3 main.py

Change the default screen to use
--------------------------------

You can set an environment variable named `KIVY_BCM_DISPMANX_ID` in order to
change the display used to run Kivy. For example, to force the display to be
HDMI, use::

    KIVY_BCM_DISPMANX_ID=2 python3 main.py

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
