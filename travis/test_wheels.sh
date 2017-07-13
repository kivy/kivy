#!/bin/bash

echo "====================== INSTALL  AND  TEST  ======================"
# install all other python versions if enough of remaining built time

# install GStreamer manually, hopefully rpath won't make problems
yes | sudo add-apt-repository ppa:gstreamer-developers/ppa
sudo apt-get -y install libgstreamer1.0-dev gstreamer1.0-alsa gstreamer1.0-plugins-base

# note: this needs reformatting for a list of python versions, later
pip install $(pwd)/wheelhouse/Kivy-1.10.1.dev0-cp27-cp27mu-manylinux1_x86_64.whl
pip install $(pwd)/wheelhouse/kivy.deps.sdl2-0.0.1-cp27-cp27mu-*.whl

# change folder, so that nose doens't detect cloned repo
pushd /home/travis/
echo "Libs from installed wheel:"
ls -lah /opt/python/2.7.13/lib/python2.7/site-packages/kivy/deps/

echo "Tests from installed wheel:"
ls -lah /opt/python/2.7.13/lib/python2.7/site-packages/kivy/tests/

# test specific folder(s) in the installed packages
nosetests -w /opt/python/2.7.13/lib/python2.7/site-packages/kivy/tests
popd


echo "====================== TEST  SCRIPT  ENDED ======================"
