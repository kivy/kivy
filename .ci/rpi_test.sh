#!/bin/bash

set -e -x
cd /io;

yes | add-apt-repository ppa:gstreamer-developers/ppa;
apt update;
apt -y install libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev libsdl2-mixer-dev;
apt -y install libgstreamer1.0-dev gstreamer1.0-alsa gstreamer1.0-plugins-base;
apt -y install python3 python3-dev libsmpeg-dev libswscale-dev libavformat-dev libavcodec-dev libjpeg-dev libtiff4-dev libX11-dev libmtdev-dev;
apt -y install python3-setuptools build-essential libgl1-mesa-dev libgles2-mesa-dev;
apt -y install xvfb pulseaudio xsel;
export CYTHON_INSTALL=$(KIVY_NO_CONSOLELOG=1 python3 -c "from kivy.tools.packaging.cython_cfg import get_cython_versions; print(get_cython_versions()[0])"  --config "kivy:log_level:error");
python3 -m pip install -I "$CYTHON_INSTALL";
python3 -m pip install --upgrade pillow pytest coveralls docutils PyInstaller;

export DISPLAY=:99.0;
/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -screen 0 1280x720x24 -ac +extension GLX;
export PYTHONPATH=$PYTHONPATH:$(pwd);

make;
KIVY_WINDOW=sdl2 make test;
make test;
