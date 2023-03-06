#!/bin/bash
set -e -x

# manylinux SDL2
MANYLINUX__SDL2__VERSION="2.24.2"
MANYLINUX__SDL2__URL="https://github.com/libsdl-org/SDL/releases/download/release-$MANYLINUX__SDL2__VERSION/SDL2-$MANYLINUX__SDL2__VERSION.tar.gz"
MANYLINUX__SDL2__FOLDER="SDL2-$MANYLINUX__SDL2__VERSION"

# manylinux SDL2_image
MANYLINUX__SDL2_IMAGE__VERSION="2.6.2"
MANYLINUX__SDL2_IMAGE__URL="https://github.com/libsdl-org/SDL_image/releases/download/release-$MANYLINUX__SDL2_IMAGE__VERSION/SDL2_image-$MANYLINUX__SDL2_IMAGE__VERSION.tar.gz"
MANYLINUX__SDL2_IMAGE__FOLDER="SDL2_image-2.6.2"

# manylinux SDL2_mixer
MANYLINUX__SDL2_MIXER__VERSION="2.6.2"
MANYLINUX__SDL2_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/releases/download/release-$MANYLINUX__SDL2_MIXER__VERSION/SDL2_mixer-$MANYLINUX__SDL2_MIXER__VERSION.tar.gz"
MANYLINUX__SDL2_MIXER__FOLDER="SDL2_mixer-2.6.2"

# manylinux SDL2_ttf
MANYLINUX__SDL2_TTF__VERSION="2.20.1"
MANYLINUX__SDL2_TTF__URL="https://github.com/libsdl-org/SDL_ttf/releases/download/release-$MANYLINUX__SDL2_TTF__VERSION/SDL2_ttf-$MANYLINUX__SDL2_TTF__VERSION.tar.gz"
MANYLINUX__SDL2_TTF__FOLDER="SDL2_ttf-2.20.1"

# Clean the dependencies folder
rm -rf kivy-dependencies

# Create the dependencies folder
mkdir kivy-dependencies

# Download the dependencies
echo "Downloading dependencies..."
mkdir kivy-dependencies/download
pushd kivy-dependencies/download
curl -L $MANYLINUX__SDL2__URL -o "${MANYLINUX__SDL2__FOLDER}.tar.gz"
curl -L $MANYLINUX__SDL2_IMAGE__URL -o "${MANYLINUX__SDL2_IMAGE__FOLDER}.tar.gz"
curl -L $MANYLINUX__SDL2_MIXER__URL -o "${MANYLINUX__SDL2_MIXER__FOLDER}.tar.gz"
curl -L $MANYLINUX__SDL2_TTF__URL -o "${MANYLINUX__SDL2_TTF__FOLDER}.tar.gz"
popd

# Extract the dependencies into build folder
echo "Extracting dependencies..."
mkdir kivy-dependencies/build
pushd kivy-dependencies/build
tar -xzf ../download/${MANYLINUX__SDL2__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__SDL2_IMAGE__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__SDL2_MIXER__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__SDL2_TTF__FOLDER}.tar.gz
popd

# Create distribution folder
echo "Creating distribution folder..."
mkdir kivy-dependencies/dist
DIST_FOLDER="$(pwd)/kivy-dependencies/dist"

# Build the dependencies
pushd kivy-dependencies/build


export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIST_FOLDER/lib;

echo "-- Build SDL2"
pushd $MANYLINUX__SDL2__FOLDER
./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin"  --enable-alsa-shared=no  --enable-jack-shared=no  --enable-pulseaudio-shared=no  --enable-esd-shared=no  --enable-arts-shared=no  --enable-nas-shared=no  --enable-sndio-shared=no  --enable-fusionsound-shared=no  --enable-libsamplerate-shared=no  --enable-wayland-shared=no --enable-x11-shared=no --enable-directfb-shared=no --enable-kmsdrm-shared=no;
make;
make install;
make distclean;
popd

echo "-- Build SDL2_mixer"
pushd $MANYLINUX__SDL2_MIXER__FOLDER
  ./external/download.sh;
  echo "-- Build SDL2_mixer - libmodplug"
  pushd external/libmodplug
    autoreconf -i;
    PATH="$DIST_FOLDER/bin:$PATH" PKG_CONFIG_PATH="$DIST_FOLDER/lib/pkgconfig" ./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin";
    PATH="$DIST_FOLDER/bin:$PATH" make;
    make install;
  popd
  PATH="$DIST_FOLDER/bin:$PATH" PKG_CONFIG_PATH="$DIST_FOLDER/lib/pkgconfig" ./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin" --enable-music-mod-modplug-shared=no --enable-music-mod-mikmod-shared=no --enable-music-midi-fluidsynth-shared=no --enable-music-ogg-shared=no --enable-music-flac-shared=no --enable-music-mp3-mpg123-shared=no LDFLAGS=-Wl,-rpath="$ORIGIN";
  PATH="$DIST_FOLDER/bin:$PATH" make;
  make install;
  make distclean;
popd

echo "-- Build SDL2_image"
pushd $MANYLINUX__SDL2_IMAGE__FOLDER
  ./external/download.sh;
  echo "-- Build SDL2_image - libwebp"
  pushd external/libwebp
    autoreconf -i;
    PATH="$DIST_FOLDER/bin:$PATH" PKG_CONFIG_PATH="$DIST_FOLDER/lib/pkgconfig" ./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin"
    PATH="$DIST_FOLDER/bin:$PATH" make;
    make install;
  popd
  echo "-- Build SDL2_image - libtiff"
  pushd external/libtiff
    autoreconf -i;
    PATH="$DIST_FOLDER/bin:$PATH" PKG_CONFIG_PATH="$DIST_FOLDER/lib/pkgconfig" ./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin"
    PATH="$DIST_FOLDER/bin:$PATH" make;
    make install;
  popd
  autoreconf -i
  PATH="$DIST_FOLDER/bin:$PATH" PKG_CONFIG_PATH="$DIST_FOLDER/lib/pkgconfig" ./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin" --enable-png-shared=no --enable-jpg-shared=no --enable-tif-shared=no --enable-webp-shared=no LDFLAGS=-Wl,-rpath="$ORIGIN";
  PATH="$DIST_FOLDER/bin:$PATH" make;
  make install;
  make distclean;
popd

echo "-- Build SDL2_ttf"
pushd $MANYLINUX__SDL2_TTF__FOLDER
  PATH="$DIST_FOLDER/bin:$PATH" PKG_CONFIG_PATH="$DIST_FOLDER/lib/pkgconfig" ./configure --prefix="$DIST_FOLDER" --bindir="$DIST_FOLDER/bin";
  PATH="$DIST_FOLDER/bin:$PATH" make;
  make install;
  make distclean;
popd

popd