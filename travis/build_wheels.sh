#!/bin/bash

echo "====================== DOCKER BUILD STARTS ======================"
echo "====================== AVAILABLE  PACKAGES ======================"
yum list installed

# orig folder
export ORIG_FOLD=$(pwd)
echo $ORIG_FOLD


echo "====================== DOWNLADING NEW ONES ======================"

# add nux-desktop repo (for ffmpeg)
rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm
yum repolist

# add EPEL repo (SDL2* packages) https://centos.pkgs.org/7/epel-x86_64/
wget http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
rpm -Uvh epel-release*rpm

# get RPM
yum check-update
yum install -y \
    cmake \
    gcc \
    gcc-c++ \
    mesa-libGLU \
    mesa-libGLU-devel \
    mesa-libGL \
    mesa-libGL-devel \
    mesa-libGLES \
    mesa-libGLES-devel \
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
    fcitx-libs \
    ffmpeg \
    ffmpeg-devel \
    smpeg-devel \
    gstreamer \
    gstreamer-devel \
    gstreamer-plugins-bad-free \
    gstreamer-plugins-bad-free-devel \
    gstreamer-plugins-base \
    gstreamer-plugins-base-devel \
    gstreamer-plugins-base-tools \
    gstreamer-plugins-good \
    gstreamer-plugins-good-devel \
    gstreamer-python \
    gstreamer-python-devel \
    gstreamer-tools \
    gstreamer1 \
    gstreamer1-devel \
    gstreamer1-plugins-bad-free \
    gstreamer1-plugins-bad-free-devel \
    gstreamer1-plugins-base \
    gstreamer1-plugins-base-devel \
    gstreamer1-plugins-base-tools \
    gstreamer1-plugins-good \
    gstreamer-plugins-good \
    gstreamer \
    gstreamer-python \
    SDL2 \
    SDL2 \
    SDL2_image \
    SDL2_image-devel \
    SDL2_mixer \
    SDL2_mixer-devel \
    SDL2_ttf \
    SDL2_ttf-devel \
    # maybe for future use
    # SDL2_net \
    # SDL2_net-devel \

# https://hg.libsdl.org/SDL/file/default/docs/README-linux.md#l18
yum -y install libass libass-devel autoconf automake bzip2 cmake freetype-devel gcc gcc-c++ git libtool make mercurial pkgconfig zlib-devel enca-devel fontconfig-devel openssl openssl-devel


# # Make SDL2 packages
# SDL="SDL2-2.0.5"
# TTF="SDL_ttf-2.0.14"
# MIX="SDL_mixer-2.0.1"
# IMG="SDL_image-2.0.1"
# curl -sL https://www.libsdl.org/release/${SDL}.tar.gz > ${SDL}.tar.gz
# curl -sL https://www.libsdl.org/projects/SDL_image/release/${IMG}.tar.gz > ${IMG}.tar.gz
# curl -sL https://www.libsdl.org/projects/SDL_ttf/release/${TTF}.tar.gz > ${TTF}.tar.gz
# curl -sL https://www.libsdl.org/projects/SDL_mixer/release/${MIX}.tar.gz > ${MIX}.tar.gz

# # SDL2
# tar xzf ${SDL}.tar.gz
# cd $SDL
# ./configure
# # --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
# make
# make install
# export KIVY_SDL2_PATH=$PWD
# cd ..

# # SDL image
# tar xzf ${IMG}.tar.gz
# cd $IMG
# ./configure
# # --enable-png --disable-png-shared --enable-jpg --disable-jpg-shared
# make
# make install
# export KIVY_SDL2_PATH=$KIVY_SDL2_PATH:$PWD
# cd ..

# # SDL ttf
# tar xzf ${TTF}.tar.gz
# cd $TTF
# ./configure
# make
# make install
# export KIVY_SDL2_PATH=$KIVY_SDL2_PATH:$PWD
# cd ..

# # SDL mixer
# tar xzf ${MIX}.tar.gz
# cd $MIX
# ./configure --enable-music-mod --disable-music-mod-shared \
            # --enable-music-ogg  --disable-music-ogg-shared \
            # --enable-music-flac  --disable-music-flac-shared \
            # --enable-music-mp3  --disable-music-mp3-shared
# make
# make install
# cd ..
# # end SDL2

PYTHONS="cp27-cp27mu cp34-cp34m cp35-cp35m cp36-cp36m"
mkdir libless_wheelhouse


echo "====================== BUILDING NEW WHEELS ======================"
for PY in $PYTHONS; do
    rm -rf /io/Setup /io/build/
    PYBIN="/opt/python/${PY}/bin"
    "${PYBIN}/pip" install --upgrade cython nose
    "${PYBIN}/pip" wheel /io/ --wheel-dir libless_wheelhouse
done;

ls -lah libless_wheelhouse


echo "====================== INCLUDING LIBRARIES ======================"
# we HAVE TO change the policy...
# or compile everything (even Mesa) by hand on CentOS 5.x
cp /io/travis/custom_policy.json /opt/_internal/cpython-3.6.0/lib/python3.6/site-packages/auditwheel/policy/policy.json

# Bundle external shared libraries into the wheels
# repair only Kivy wheel (pure py wheels such as Kivy_Garden kill the build)
for whl in libless_wheelhouse/Kivy-*.whl; do
    echo "Show:"
    auditwheel show "$whl"
    echo "Repair:"
    auditwheel repair "$whl" -w /io/wheelhouse/
done;

ls -lah /io/wheelhouse

# Docker doesn't allow creating a video device / display, therefore we need
# to test outside of the container i.e. on Ubuntu, which is even better,
# because there is no pre-installed stuff necessary for building the wheels
# + it's a check if the wheels work on other distro(s).


echo "====================== CREATING LIB WHEELS ======================"
# Move some libs out of the .whl archive and put them into separate wheels
for whl in /io/wheelhouse/Kivy-*.whl; do
    # prepare the content
    mkdir sdl2_whl
    unzip "$whl" -d whl_tmp

    # SDL2 + image + mixer + ttf
    cp whl_tmp/kivy/.libs/libSDL2* sdl2_whl

    # SDL2 deps
    cp whl_tmp/kivy/.libs/libfreetype* sdl2_whl
    cp whl_tmp/kivy/.libs/libjbig* sdl2_whl
    cp whl_tmp/kivy/.libs/libjpeg* sdl2_whl
    cp whl_tmp/kivy/.libs/libpng* sdl2_whl
    cp whl_tmp/kivy/.libs/libtiff* sdl2_whl
    cp whl_tmp/kivy/.libs/libwebp* sdl2_whl
    cp whl_tmp/kivy/.libs/libz* sdl2_whl

    # remove folder
    rm -rf whl_tmp


    # create setup.py
    python "/io/travis/libs_wheel.py" "$(pwd)/sdl2_whl" "kivy.libs.sdl2" "zlib"

    # create wheels for each Python version
    for PY in $PYTHONS; do
        PYBIN="/opt/python/${PY}/bin"
        "${PYBIN}/pip" wheel sdl2_whl --wheel-dir /io/wheelhouse/
    done;


    # remove specific libs from now Kivy + basic libs only wheel
    zip -d "$whl" \
        kivy/.libs/libSDL2* kivy/.libs/libfreetype* kivy/.libs/libjbig* \
        kivy/.libs/libjpeg* kivy/.libs/libpng* kivy/.libs/libz* \
        kivy/.libs/libtiff* kivy/.libs/libwebp*

    # remove GStreamer
    zip -d "$whl" \
    kivy/.libs/libgmodule* kivy/.libs/libgstreamer*

    # clean folders
    rm -rf sdl2_whl
done;

ls -lah /io/wheelhouse


echo "====================== BACKING UP PACKAGES ======================"
# ##
# note: if it all works, just backup all required AND installed RPMs somewhere
# in case of another EOL until ported to newer OS.
# ##
yum install -y yum-utils
mkdir backup && pushd backup
yumdownloader --destdir . --resolve \
    cmake \
    gcc \
    gcc-c++ \
    mesa-libGLU \
    mesa-libGLU-devel \
    mesa-libGL \
    mesa-libGL-devel \
    mesa-libGLES \
    mesa-libGLES-devel \
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
    fcitx-libs \
    ffmpeg \
    ffmpeg-devel \
    smpeg-devel \
    gstreamer \
    gstreamer-devel \
    gstreamer-plugins-bad-free \
    gstreamer-plugins-bad-free-devel \
    gstreamer-plugins-base \
    gstreamer-plugins-base-devel \
    gstreamer-plugins-base-tools \
    gstreamer-plugins-good \
    gstreamer-plugins-good-devel \
    gstreamer-python \
    gstreamer-python-devel \
    gstreamer-tools \
    gstreamer1 \
    gstreamer1-devel \
    gstreamer1-plugins-bad-free \
    gstreamer1-plugins-bad-free-devel \
    gstreamer1-plugins-base \
    gstreamer1-plugins-base-devel \
    gstreamer1-plugins-base-tools \
    gstreamer1-plugins-good \
    gstreamer-plugins-good \
    gstreamer \
    gstreamer-python \
    SDL2 \
    SDL2 \
    SDL2_image \
    SDL2_image-devel \
    SDL2_mixer \
    SDL2_mixer-devel \
    SDL2_ttf \
    SDL2_ttf-devel \
    libass \
    libass-devel \
    autoconf \
    automake \
    bzip2 \
    freetype-devel \
    git \
    make \
    mercurial \
    pkgconfig \
    zlib-devel \
    enca-devel \
    fontconfig-devel \
    openssl \
    openssl-devel

# show downloaded RPMs + details
ls -lah .
popd


echo "====================== DOCKER BUILD  ENDED ======================"
