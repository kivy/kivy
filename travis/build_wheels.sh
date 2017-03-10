#!/bin/bash

# Install a system package required by our library
yum list installed

# get RPM FORGE
MIRROR="http://repoforge.mirror.digitalpacific.com.au/"
ARCH="uname -m"
echo ${ARCH}

## get GPG
wget ${MIRROR}RPM-GPG-KEY.dag.txt
rpm --import RPM-GPG-KEY.dag.txt

## get RPM
wget ${MIRROR}redhat/el5/en/${arch}/rpmforge/RPMS/rpmforge-release-0.5.3-1.el5.rf.${arch}.rpm
rpm -Uvh rpmforge-release-0.5.3-1.el5.rf.${arch}.rpm

yum check-update
yum search pulseaudio

rpm -ivh pulseaudio-0.9.5-5.el5.kb.i386.rpm
rpm -ivh pulseaudio-0.9.5-5.el5.kb.x86_64.rpm

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
    ffmpeg \
    ffmpeg-devel
#    libedit \

# missing libs, compile?
## -dev
yum search smpeg
yum search swscale
yum search avformat
yum search avcodec
yum search mtdev
yum search asound2
yum search esd0
yum search udev
yum search ibus-1.0
yum search fcitx-libs

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
export KIVY_SDL2_PATH=$PWD
cd ..

# SDL image
tar xzf ${IMG}.tar.gz
cd $IMG
./configure
# --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
make
make install
export KIVY_SDL2_PATH=$KIVY_SDL2_PATH:$PWD
cd ..

# SDL ttf
tar xzf ${TTF}.tar.gz
cd $TTF
./configure
make
make install
export KIVY_SDL2_PATH=$KIVY_SDL2_PATH:$PWD
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

PYTHONS="cp27-cp27mu cp34-cp34m cp35-cp35m cp36-cp36m"

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
