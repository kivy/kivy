#!/bin/bash

yum list installed

# ##
# note: if it all works, just backup all required AND installed RPMs somewhere
#
# yum install -y yum-utils
# mkdir backup && cd backup
# yumdownloader --resolve <package>
# ##

# orig folder
export ORIG_FOLD=$(pwd)
echo $ORIG_FOLD

# enable display
export DISPLAY=:99.0
/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -screen 0 1280x720x24 -ac +extension GLX;      

# add nux-desktop repo (for ffmpeg)
rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm
yum repolist

# add EPEL repo (SDL2* packages) https://centos.pkgs.org/7/epel-x86_64/
wget http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
rpm -Uvh epel-release*rpm

# get RPM
yum check-update
yum search pulseaudio

yum install -y \
    cmake \
    gcc \
    gcc-c++ \
    mesa-libGLU \
    mesa-libGLU-devel \
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


mkdir wheelhouse
echo $(pwd)
ls $(pwd)/wheelhouse

# Compile wheels
echo "Building wheels:"
for PY in $PYTHONS; do
    rm -rf /io/Setup /io/build/
    PYBIN="/opt/python/${PY}/bin"
    "${PYBIN}/pip" install --upgrade cython nose
    "${PYBIN}/pip" wheel /io/ --wheel-dir wheelhouse/ --verbose
done

cp ./travis/custom_policy.json /usr/local/lib/python3.6/site-packages/auditwheel/policy/policy.json

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
echo "Installing and testing:"
ls $(pwd)/wheelhouse
for PY in $PYTHONS; do
    PYBIN="/opt/python/${PY}/bin/"
    "${PYBIN}/pip" install "/wheelhouse/Kivy-1.10.1.dev0-${PY}-linux_x86_64.whl" --verbose
    cd $HOME
    "${PYBIN}/nosetests" kivy
    cd $ORIG_FOLD
done

# # Bundle external shared libraries into the wheels
# for whl in wheelhouse/*.whl; do
    # auditwheel repair "$whl" -w /io/wheelhouse/
# done
