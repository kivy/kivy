#!/bin/bash

# Install a system package required by our library
wget ftp://mirror.switch.ch/pool/4/mirror/fedora/linux/releases/25/Everything/x86_64/os/Packages/s/SDL2-devel-2.0.5-2.fc25.i686.rpm
wget ftp://mirror.switch.ch/pool/4/mirror/fedora/linux/releases/25/Everything/x86_64/os/Packages/s/SDL2-devel-2.0.5-2.fc25.x86_64.rpm

wget ftp://mirror.switch.ch/pool/4/mirror/fedora/linux/releases/24/Everything/x86_64/os/Packages/s/SDL2_mixer-devel-2.0.1-2.fc24.x86_64.rpm
wget ftp://mirror.switch.ch/pool/4/mirror/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/s/SDL2_mixer-devel-2.0.1-2.fc24.i686.rpm

wget ftp://mirror.switch.ch/pool/4/mirror/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/s/SDL2_ttf-devel-2.0.14-2.fc25.i686.rpm
wget ftp://mirror.switch.ch/pool/4/mirror/fedora/linux/development/rawhide/Everything/x86_64/os/Packages/s/SDL2_ttf-devel-2.0.14-2.fc25.x86_64.rpm

rpm -ivh SDL2-devel-2.0.5-2.fc25.i686.rpm
rpm -ivh SDL2-devel-2.0.5-2.fc25.x86_64.rpm

rpm -ivh SDL2_mixer-devel-2.0.1-2.fc24.x86_64.rpm
rpm -ivh SDL2_mixer-devel-2.0.1-2.fc24.i686.rpm

rpm -ivh SDL2_ttf-devel-2.0.14-2.fc25.i686.rpm
rpm -ivh SDL2_ttf-devel-2.0.14-2.fc25.x86_64.rpm

yum check-update
yum install \
    make \
    mercurial \
    automake \
    gcc \
    gcc-c++ \
    khrplatform-devel \
    mesa-libGLES \
    mesa-libGLES-devel \
    gstreamer-plugins-good \
    gstreamer \
    gstreamer-python \
    mtdev-devel \
    python-devel \
    python-pip

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install --upgrade cython nose
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    "${PYBIN}/pip" install . --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/nosetests" kivy)
done
