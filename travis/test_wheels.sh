#!/bin/bash

echo "Testing wheels:"
pip show -vvv $(pwd)/wheelhouse/Kivy-1.10.1.dev0-cp27-cp27mu-manylinux1_x86_64.whl
pip install -vvv $(pwd)/wheelhouse/Kivy-1.10.1.dev0-cp27-cp27mu-manylinux1_x86_64.whl
cd /
nosetests kivy
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
LD_LIBRARY_PATH=/home/travis/build/KeyWeeUsr/kivy/.lib/:/home/travis/build/KeyWeeUsr/kivy/kivy/.lib/:/opt/python/2.7.13/lib/python2.7/site-packages/kivy/.lib/:/opt/python/2.7.13/lib/python2.7/site-packages/kivy/kivy/.lib:$LD_LIBRARY_PATH nosetests kivy
