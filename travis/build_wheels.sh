#!/bin/bash

echo "====================== DOCKER BUILD STARTS ======================"
echo "====================== AVAILABLE  PACKAGES ======================"
yum list installed


echo "====================== DOWNLADING NEW ONES ======================"

# add nux-desktop repo (only for ffmpeg)
# http://li.nux.ro/download/nux/dextop/el7/x86_64/
rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm
yum repolist

# add EPEL repo (SDL2* packages) https://centos.pkgs.org/7/epel-x86_64/
#wget http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
#rpm -Uvh epel-release*rpm

# repo: http://mirror.centos.org/centos/7/os/x86_64/Packages/
yum check-update

# general stuff
yum install -y \
    gcc \
    gcc-c++ \
    git \
    pkgconfig \
    python-devel \
    dbus-devel \
    xorg-x11-server-Xvfb
# ok ok ok ok ok ok ok

# general SDL2 stuff
# https://hg.libsdl.org/SDL/file/default/docs/README-linux.md#l18
yum install -y \
    mercurial \
    make \
    cmake \
    autoconf \
    automake \
    libtool \
    libedit \
    libass \
    libass-devel \
    pulseaudio \
    pulseaudio-libs \
    pulseaudio-libs-devel \
    libX11-devel \
    libXext-devel \
    libXrandr-devel \
    libXcursor-devel \
    libXi-devel \
    libXinerama-devel \
    libXxf86vm-devel \
    libXScrnSaver-devel \
    mesa-libGL \
    mesa-libGL-devel \
    esd0-devel \
    udev-devel \
    mesa-libGLU \
    mesa-libGLU-devel \
    mesa-libGLES \
    mesa-libGLES-devel \
    ibus-1.0-devel \
    fcitx-libs \
    libsamplerate-devel
# ok ok ok ok ok ok ok no no ok ok ok ok ok ok ok ok
# ok ok ok ok ok no no ok ok ok ok ok ok ok no ok

# SDL2 image
yum install -y \
    libtiff-devel \
    libpng-devel \
    libjpeg-devel \
    libjpeg-turbo-devel \
    libwebp-devel
# ok ok no ok ok

# SDL2 mixer
yum install -y \
    libvorbis-devel
# ok

# SDL2 ttf
yum install -y \
    freetype-devel
# ok

# SDL2
yum install -y \
    systemd-devel \
    mesa-libEGL \
    mesa-libEGL-devel \
    libxkbcommon-devel \
    alsa-lib-devel
# ok ok ok no ok

# FFMpeg
# libavcodec.so libavdevice.so libavfilter.so libavformat.so libavresample.so
# libavutil.so libpostproc.so libswresample.so libswscale.so
yum install -y ffmpeg-devel

yum install -y \
    mtdev-devel \
    ffmpeg \
    smpeg-devel \
    bzip2 \
    bzip2-devel \
    zlib-devel \
    enca-devel \
    fontconfig-devel \
    openssl \
    openssl-devel
# ok ok no ok ok ok no ok ok ok

# GStreamer
# gstreamer1.0-alsa is in gstreamer1-plugins-base
yum install -y \
    gstreamer1-devel \
    gstreamer1-plugins-base \
    gstreamer1-plugins-base-devel
# ok ok ok


# Make SDL2 packages
SDL="SDL2-2.0.5"
IMG="SDL2_image-2.0.1"
TTF="SDL2_ttf-2.0.14"
MIX="SDL2_mixer-2.0.1"
wget https://www.libsdl.org/release/${SDL}.tar.gz
wget https://www.libsdl.org/projects/SDL_image/release/${IMG}.tar.gz
wget https://www.libsdl.org/projects/SDL_ttf/release/${TTF}.tar.gz
wget https://www.libsdl.org/projects/SDL_mixer/release/${MIX}.tar.gz

# SDL2 (after IMG, TTF, MIX)
tar xzf ${SDL}.tar.gz
pushd $SDL
# https://hg.libsdl.org/SDL/file/a0327860b8fb/debian/rules
./configure --disable-rpath \
            --enable-sdl-dlopen \
            --disable-loadso \
            --disable-nas \
            --disable-esd \
            --disable-arts \
            --disable-alsa-shared \
            --disable-pulseaudio-shared \
            --enable-ibus \
            --disable-x11-shared \
            --disable-video-directfb \
            --enable-video-opengles \
            --disable-video-wayland
make -j4
make install
popd

# SDL image
tar xzf ${IMG}.tar.gz
pushd $IMG
# https://hg.libsdl.org/SDL_image/file/6332f9425dcc/debian/rules
./configure --disable-webp \
            --disable-jpg-shared \
            --disable-png-shared \
            --disable-tif-shared
make
make install
popd

# SDL ttf
tar xzf ${TTF}.tar.gz
pushd $TTF
# https://hg.libsdl.org/SDL_ttf/file/3b93536d291a/debian/rules
./configure
make
make install
popd

# SDL mixer
tar xzf ${MIX}.tar.gz
pushd $MIX
# https://hg.libsdl.org/SDL_mixer/file/15571e1ac71f/debian/rules
./configure --enable-music-cmd \
            --enable-music-mp3 \
            --enable-music-mp3-smpeg \
            --disable-music-mp3-mad-gpl \
            --enable-music-mod \
            --enable-music-mod-modplug \
            --disable-music-mod-mikmod \
            --enable-music-ogg \
            --enable-music-wave \
            --enable-music-midi \
            --enable-music-midi-fluidsynth \
            --enable-music-midi-timidity \
            --disable-music-flac-shared \
            --disable-music-ogg-shared \
            --disable-music-mp3-smpeg-shared \
            --disable-music-mod-mikmod-shared \
            --disable-music-mod-modplug-shared \
            --disable-music-midi-fluidsynth-shared \
make
make install
popd
# end SDL2


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
    auditwheel repair "$whl" -w /io/wheelhouse/ --lib-sdir "deps"
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
    unzip "$whl" -d whl_tmp > /dev/null


    # SDL2 folder
    mkdir sdl2_whl
    mkdir sdl2_whl/kivy
    mkdir sdl2_whl/kivy/deps
    mkdir sdl2_whl/kivy/deps/sdl2
    touch sdl2_whl/kivy/deps/sdl2/__init__.py

    # SDL2 + image + mixer + ttf
    cp whl_tmp/kivy/deps/libSDL2* sdl2_whl/kivy/deps

    # SDL2 deps
    cp whl_tmp/kivy/deps/libfreetype* sdl2_whl/kivy/deps
    cp whl_tmp/kivy/deps/libjbig* sdl2_whl/kivy/deps
    cp whl_tmp/kivy/deps/libjpeg* sdl2_whl/kivy/deps
    cp whl_tmp/kivy/deps/libpng* sdl2_whl/kivy/deps
    cp whl_tmp/kivy/deps/libtiff* sdl2_whl/kivy/deps
    cp whl_tmp/kivy/deps/libwebp* sdl2_whl/kivy/deps
    cp whl_tmp/kivy/deps/libz* sdl2_whl/kivy/deps


    # GStreamer folder
    mkdir gstreamer_whl
    mkdir gstreamer_whl/kivy
    mkdir gstreamer_whl/kivy/deps
    mkdir gstreamer_whl/kivy/deps/gstreamer
    touch gstreamer_whl/kivy/deps/gstreamer/__init__.py

    # GStreamer
    cp whl_tmp/kivy/deps/libgmodule* gstreamer_whl/kivy/deps
    cp whl_tmp/kivy/deps/libgst* gstreamer_whl/kivy/deps

    # remove folder
    rm -rf whl_tmp


    # create setup.py
    python "/io/travis/libs_wheel.py" "$(pwd)/sdl2_whl" "kivy.deps.sdl2" "zlib"
    python "/io/travis/libs_wheel.py" "$(pwd)/gstreamer_whl" "kivy.deps.gstreamer" "LGPL"

    # create wheels for each Python version
    pushd sdl2_whl

    for PY in $PYTHONS; do
        PYBIN="/opt/python/${PY}/bin"
        "${PYBIN}/python" setup.py bdist_wheel -d /io/wheelhouse/
    done;

    popd

    # create wheels for each Python version
    pushd gstreamer_whl

    for PY in $PYTHONS; do
        PYBIN="/opt/python/${PY}/bin"
        "${PYBIN}/python" setup.py bdist_wheel -d /io/wheelhouse/
    done;

    popd

    # remove specific libs from now Kivy + basic libs only wheel
    # remove SDL2
    zip -d "$whl" \
        kivy/deps/libSDL2* kivy/deps/libfreetype* kivy/deps/libjbig* \
        kivy/deps/libjpeg* kivy/deps/libpng* kivy/deps/libz* \
        kivy/deps/libtiff* kivy/deps/libwebp*

    # remove GStreamer
    zip -d "$whl" \
    kivy/deps/libgmodule* kivy/deps/libgstreamer*

    # clean folders
    rm -rf sdl2_whl
    rm -rf gstreamer_whl
done;

ls -lah /io/wheelhouse


echo "====================== BACKING UP PACKAGES ======================"
ls -lah /var/cache/yum
# # ##
# # note: if it all works, just backup all required AND installed RPMs somewhere
# # in case of another EOL until ported to newer OS.
# # ##
# yum install -y yum-utils
# mkdir backup && pushd backup
# yumdownloader --destdir . --resolve \
    # cmake \
    # gcc \
    # gcc-c++ \
    # mesa-libGLU \
    # mesa-libGLU-devel \
    # mesa-libGL \
    # mesa-libGL-devel \
    # mesa-libGLES \
    # mesa-libGLES-devel \
    # python-devel \
    # dbus-devel \
    # xorg-x11-server-Xvfb \
    # libXext-devel \
    # libXrandr-devel \
    # libXcursor-devel \
    # libXinerama-devel \
    # libXxf86vm-devel \
    # libXScrnSaver-devel \
    # libsamplerate-devel \
    # libjpeg-devel \
    # libtiff-devel \
    # libX11-devel \
    # libXi-devel \
    # libtool \
    # libedit \
    # pulseaudio \
    # pulseaudio-devel \
    # swscale-devel \
    # avformat-devel \
    # avcodev-devel \
    # mtdev-devel \
    # esd0-devel \
    # udev-devel \
    # ibus-1.0-devel \
    # fcitx-libs \
    # ffmpeg \
    # ffmpeg-devel \
    # smpeg-devel \
    # gstreamer1-devel \
    # gstreamer1-plugins-base \
    # gstreamer1-plugins-base-devel \
    # SDL2 \
    # SDL2-devel \
    # SDL2_image \
    # SDL2_image-devel \
    # SDL2_mixer \
    # SDL2_mixer-devel \
    # SDL2_ttf \
    # SDL2_ttf-devel \
    # libass \
    # libass-devel \
    # autoconf \
    # automake \
    # bzip2 \
    # freetype-devel \
    # git \
    # make \
    # mercurial \
    # pkgconfig \
    # zlib-devel \
    # enca-devel \
    # fontconfig-devel \
    # openssl \
    # openssl-devel

# # show downloaded RPMs + details
# ls -lah .
# popd


echo "====================== DOCKER BUILD  ENDED ======================"
