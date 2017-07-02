#!/bin/bash

yum list installed

## get RPM
yum check-update
yum search pulseaudio

yum install -y \
    cmake \
    gcc \
    gcc-c++ \
    mesa-libGLU \
    mesa-libGLU-devel \
    gstreamer-plugins-good \
    gstreamer \
    gstreamer-python \
    python-devel \
    dbus-devel \
    xorg-x11-server-Xvfb \
    libXext-devel \
    libXrandr-devel \
    libXcursor-devel \
    libXinerama-devel \
    libXxf86vm-devel \
    libXScrnSaver-devel \
    libsamplerate-devel \
    libjpeg-devel \
    libtiff-devel \
    libX11-devel \
    libXi-devel \
    libtool \
    libedit \
    pulseaudio \
    pulseaudio-devel \
    swscale-devel \
    avformat-devel \
    avcodev-devel \
    mtdev-devel \
    esd0-devel \
    udev-devel \
    ibus-1.0-devel \
    fcitx-libs
    

# from Forge
yum install -y \
    ffmpeg \
    ffmpeg-devel \
    smpeg-devel

# https://hg.libsdl.org/SDL/file/default/docs/README-linux.md#l18
yum -y install libass libass-devel autoconf automake bzip2 cmake freetype-devel gcc gcc-c++ git libtool make mercurial pkgconfig zlib-devel enca-devel fontconfig-devel openssl openssl-devel

PYTHONS="cp27-cp27mu cp34-cp34m cp35-cp35m cp36-cp36m"

mkdir wheelhouse
# Compile wheels
for PY in $PYTHONS; do
    rm -rf /io/Setup /io/build/
    PYBIN="/opt/python/${PY}/bin"
    "${PYBIN}/pip" install --upgrade cython nose
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
for PY in $PYTHONS; do
    PYBIN="/opt/python/${PYBIN}/bin/"
    "${PYBIN}/pip" install . --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/nosetests" kivy)
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done
