#!/bin/bash

echo "Testing wheels:"
pip install $(pwd)/wheelhouse/Kivy-1.10.1.dev0-cp27-cp27mu-manylinux1_x86_64.whl --verbose
cd ../..
nosetests kivy
