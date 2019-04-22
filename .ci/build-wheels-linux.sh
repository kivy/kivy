#!/bin/bash
set -e -x

yum -y install  autoconf automake cmake gcc gcc-c++ git make pkgconfig zlib-devel portmidi portmidi-devel Xorg-x11-server-deve mesa-libEGL-devel mtdev-devel mesa-libEGL freetype freetype-devel openjpeg openjpeg-devel libpng libpng-devel libtiff libtiff-devel libwebp libwebp-devel dbus-devel dbus ibus-devel ibus libsamplerate-devel libsamplerate libudev-devel libudev libmodplug-devel libmodplug libvorbis-devel libvorbis flac-devel flac libjpeg-turbo-devel libjpeg-turbo wget;
mkdir ~/kivy_sources;
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/kivy_build/lib;

cd ~/kivy_sources;
git clone --depth 1 https://github.com/spurious/SDL-mirror.git
cd SDL-mirror;
./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin"  --enable-alsa-shared=no  --enable-jack-shared=no  --enable-pulseaudio-shared=no  --enable-esd-shared=no  --enable-arts-shared=no  --enable-nas-shared=no  --enable-sndio-shared=no  --enable-fusionsound-shared=no  --enable-libsamplerate-shared=no  --enable-wayland-shared=no --enable-x11-shared=no --enable-directfb-shared=no --enable-kmsdrm-shared=no;
make;
make install;
make distclean;

cd ~/kivy_sources;
wget http://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-2.0.4.tar.gz;
tar xzf SDL2_mixer-2.0.4.tar.gz;
cd SDL2_mixer-2.0.4;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin" --enable-music-mod-modplug-shared=no --enable-music-mod-mikmod-shared=no --enable-music-midi-fluidsynth-shared=no --enable-music-ogg-shared=no --enable-music-flac-shared=no --enable-music-mp3-mpg123-shared=no;
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

cd ~/kivy_sources;
wget http://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.0.4.tar.gz;
tar xzf SDL2_image-2.0.4.tar.gz;
cd SDL2_image-2.0.4;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin" --enable-png-shared=no --enable-jpg-shared=no --enable-tif-shared=no --enable-webp-shared=no;
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

cd ~/kivy_sources;
wget http://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.15.tar.gz;
tar xzf SDL2_ttf-2.0.15.tar.gz;
cd SDL2_ttf-2.0.15;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin";
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

cd /io;
for PYBIN in /opt/python/*3*/bin; do
    if [[ $PYBIN != *"34"* ]]; then
        "${PYBIN}/pip" install --upgrade setuptools pip;
        "${PYBIN}/pip" install --upgrade cython nose pygments docutils;
        USE_X11=1 USE_SDL2=1 USE_PANGOFT2=0 USE_GSTREAMER=0 PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" "${PYBIN}/pip" wheel --no-deps . -w wheelhouse/;
    fi
done

for name in /io/wheelhouse/*.whl; do
    echo "Fixing $name";
    auditwheel repair --plat manylinux2010_x86_64 $name -w /io/wheelhouse/;
done
