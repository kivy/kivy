#!/bin/bash
set -e -x

yum -y install  autoconf automake cmake gcc gcc-c++ git make pkgconfig zlib-devel portmidi portmidi-devel Xorg-x11-server-deve mesa-libEGL-devel mtdev-devel mesa-libEGL freetype freetype-devel openjpeg openjpeg-devel libpng libpng-devel libtiff libtiff-devel libwebp libwebp-devel dbus-devel dbus ibus-devel ibus libsamplerate-devel libsamplerate libudev-devel libudev libmodplug-devel libmodplug libvorbis-devel libvorbis flac-devel flac libjpeg-turbo-devel libjpeg-turbo wget glib2-devel cairo-devel
mkdir ~/kivy_sources;
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/kivy_build/lib;

cd ~/kivy_sources;
wget http://www.libsdl.org/release/SDL2-2.0.14.tar.gz
tar xzf SDL2-2.0.14.tar.gz
cd SDL2-2.0.14
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
wget http://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.0.5.tar.gz;
tar xzf SDL2_image-2.0.5.tar.gz;
cd SDL2_image-2.0.5;
PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin" --enable-png-shared=no --enable-jpg-shared=no --enable-tif-shared=no --enable-webp-shared=no;
PATH="$HOME/kivy_build/bin:$PATH" make;
make install;
make distclean;

# install meson
cd ~/kivy_sources
meson_python=$(ls -d /opt/python/*3*/bin | tail -1)
"$meson_python/pip" install --upgrade setuptools pip virtualenv
"$meson_python/python" -m virtualenv venv
source venv/bin/activate
pip install --upgrade meson ninja fonttools

cd ~/kivy_sources
harf_root="harfbuzz-2.8.0"
wget "https://github.com/harfbuzz/harfbuzz/releases/download/2.8.0/$harf_root.tar.xz"
tar xf "$harf_root.tar.xz"
cd "$harf_root"
meson setup build --wrap-mode=default --buildtype=release -Dglib=disabled -Dgobject=disabled -Dcairo=disabled -Dfreetype=enabled --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin"
meson compile -C build
meson install

deactivate

cd ~/kivy_sources
ttf_hash="9d2a04f157c4e0c206fe5df7103018d5a59c6e35"
wget "https://github.com/libsdl-org/SDL_ttf/archive/$ttf_hash.tar.gz"
tar xzf "$ttf_hash.tar.gz"
cd "SDL_ttf-$ttf_hash"
sed -si "s/\(define TTF_USE_HARFBUZZ\) 0/\1 1/" SDL_ttf.c
env CFLAGS="$(pkg-config --cflags harfbuzz)" LDFLAGS="$(pkg-config --libs harfbuzz)" PATH="$HOME/kivy_build/bin:$PATH" PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" ./configure --prefix="$HOME/kivy_build" --bindir="$HOME/kivy_build/bin"
PATH="$HOME/kivy_build/bin:$PATH" make
make install
make distclean

cd /io;
for PYBIN in /opt/python/*3*/bin; do
    if [[ $PYBIN != *"34"* && $PYBIN != *"35"* ]]; then
        "${PYBIN}/pip" install --upgrade setuptools pip;
        "${PYBIN}/pip" install --upgrade cython nose pygments docutils;
        USE_HARFBUZZ=1 KIVY_SPLIT_EXAMPLES=1 USE_X11=1 USE_SDL2=1 USE_PANGOFT2=0 USE_GSTREAMER=0 PKG_CONFIG_PATH="$HOME/kivy_build/lib/pkgconfig" "${PYBIN}/pip" wheel --no-deps . -w dist/;
    fi
done

for name in /io/dist/*.whl; do
    echo "Fixing $name";
    auditwheel repair --plat manylinux2014_x86_64 $name -w /io/dist/;
done
