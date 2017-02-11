#!/bin/bash

# Install a system package required by our library
yum list installed
yum check-update
# already installed:
# make \
# automake \
# autoconf \
# libX11-devel \

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

# deps from travis
# -dev
yum search libc
yum search smpeg
yum search swscale
yum search avformat
yum search avcodec
# substring v
yum search mt
yum search mtdev
yum search gl1-mesa
yum search gles2-mesa

# non -dev
yum search build-essential
yum search pulseaudio


# sdl2 deps
# non -dev libs
yum search tool
yum search libtool
# mercurial make cmake autoconf automake

# -dev libs
# substring v
yum search asound
yum search asound2
yum search pulse
yum search audio
yum search xi
# substring v
yum search esd
yum search esd0
yum search udev
# substring v
yum search ibus
yum search ibus-1.0
yum search fcitx-libs

# Not sure if khr is even needed now
yum search khr

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
./configure
# --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
make
make install
cd ..

# SDL image
tar xzf ${IMG}.tar.gz
cd $IMG
./configure
# --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
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
