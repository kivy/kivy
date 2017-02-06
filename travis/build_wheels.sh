#!/bin/bash

# Install a system package required by our library
yum check-update
yum install -y \
    make \
    cmake \
    mercurial \
    automake \
    autoconf \
    gcc \
    gcc-c++ \
    khrplatform-devel \
    mesa-libGLU \
    mesa-libGLU-devel \
    libX11-devel \
    gstreamer-plugins-good \
    gstreamer \
    gstreamer-python \
    mtdev-devel \
    python-devel \
    python-pip

# https://hg.libsdl.org/SDL/file/default/docs/README-linux.md
# libtool libasound2-dev libpulse-dev libaudio-dev libxext-dev \
# libxrandr-dev libxcursor-dev libxi-dev libxinerama-dev libxxf86vm-dev \
# libxss-dev libesd0-dev libdbus-1-dev libudev-dev libibus-1.0-dev \
# fcitx-libs-dev libsamplerate0-dev

# Make SDL2 packages
SDL="SDL2-2.0.5"
TTF="SDL_ttf-2.0.14"
MIX="SDL_mixer-2.0.1"
IMG="SDL_image-2.0.1"
curl -sL https://www.libsdl.org/release/${SDL}.tar.gz > ${SDL}.tar.gz
curl -sL https://www.libsdl.org/projects/SDL_image/release/${IMG}.tar.gz > ${IMG}.tar.gz
curl -sL https://www.libsdl.org/projects/SDL_ttf/release/${TTF}.tar.gz > ${TTF}.tar.gz
curl -sL https://www.libsdl.org/projects/SDL_mixer/release/${MIX}.tar.gz > ${MIX}.tar.gz

# SDL2
tar xzf ${SDL}.tar.gz
cd $SDL
./configure --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
make
make install
cd ..

# SDL image
tar xzf ${IMG}.tar.gz
cd $IMG
./configure --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
make
make install
cd ..

# SDL ttf
tar xzf ${TTF}.tar.gz
cd $TTF
./configure
make
make install
cd ..

# SDL mixer
tar xzf ${MIX}.tar.gz
cd $MIX
./configure --enable-music-mod --disable-music-mod-shared \
            --enable-music-ogg  --disable-music-ogg-shared \
            --enable-music-flac  --disable-music-flac-shared \
            --enable-music-mp3  --disable-music-mp3-shared
make
make install
cd ..

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
