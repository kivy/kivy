#!/bin/bash
set -e -x

yum -y install  autoconf automake cmake gcc gcc-c++ git make pkgconfig zlib-devel portmidi portmidi-devel gstreamer gstreamer-devel gstreamer-plugins-base gstreamer-plugins-base-devel gstreamer-plugins-good gstreamer-plugins-good-devel Xorg-x11-server-deve mesa-libEGL-devel mtdev-devel mesa-libEGL
mkdir ~/kivy_sources;
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/kivy_build/lib;

cd ~/kivy_sources;
git clone --depth 1 https://github.com/spurious/SDL-mirror.git
cd SDL-mirror;
./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin";
make;
make install;
make distclean;

cd ~/kivy_sources;
wget http://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-2.0.2.tar.gz;
tar xzf SDL2_mixer-2.0.2.tar.gz;
cd SDL2_mixer-2.0.2;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin";
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

cd ~/kivy_sources;
wget http://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.0.3.tar.gz;
tar xzf SDL2_image-2.0.3.tar.gz;
cd SDL2_image-2.0.3;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin";
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

cd ~/kivy_sources;
wget http://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.14.tar.gz;
tar xzf SDL2_ttf-2.0.14.tar.gz;
cd SDL2_ttf-2.0.14;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin";
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

# Compile wheels
for PYBIN in /opt/python/*3*/bin; do
    "${PYBIN}/pip" install --upgrade setuptools pip
    "${PYBIN}/pip" install --upgrade cython nose
    USE_X11=1 USE_SDL2=1 USE_GSTREAMER=1 PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done