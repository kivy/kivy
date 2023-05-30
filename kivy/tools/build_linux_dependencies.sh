#!/bin/bash
set -e -x

# manylinux SDL2
MANYLINUX__SDL2__VERSION="2.26.4"
MANYLINUX__SDL2__URL="https://github.com/libsdl-org/SDL/releases/download/release-$MANYLINUX__SDL2__VERSION/SDL2-$MANYLINUX__SDL2__VERSION.tar.gz"
MANYLINUX__SDL2__FOLDER="SDL2-$MANYLINUX__SDL2__VERSION"

# manylinux SDL2_image
MANYLINUX__SDL2_IMAGE__VERSION="2.6.3"
MANYLINUX__SDL2_IMAGE__URL="https://github.com/libsdl-org/SDL_image/releases/download/release-$MANYLINUX__SDL2_IMAGE__VERSION/SDL2_image-$MANYLINUX__SDL2_IMAGE__VERSION.tar.gz"
MANYLINUX__SDL2_IMAGE__FOLDER="SDL2_image-$MANYLINUX__SDL2_IMAGE__VERSION"

# manylinux SDL2_mixer
MANYLINUX__SDL2_MIXER__VERSION="2.6.3"
MANYLINUX__SDL2_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/releases/download/release-$MANYLINUX__SDL2_MIXER__VERSION/SDL2_mixer-$MANYLINUX__SDL2_MIXER__VERSION.tar.gz"
MANYLINUX__SDL2_MIXER__FOLDER="SDL2_mixer-$MANYLINUX__SDL2_MIXER__VERSION"

# manylinux SDL2_ttf
MANYLINUX__SDL2_TTF__VERSION="2.20.2"
MANYLINUX__SDL2_TTF__URL="https://github.com/libsdl-org/SDL_ttf/releases/download/release-$MANYLINUX__SDL2_TTF__VERSION/SDL2_ttf-$MANYLINUX__SDL2_TTF__VERSION.tar.gz"
MANYLINUX__SDL2_TTF__FOLDER="SDL2_ttf-$MANYLINUX__SDL2_TTF__VERSION"

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

# Build the dependencies
pushd kivy-dependencies/build

echo "-- Build SDL2"
pushd $MANYLINUX__SDL2__FOLDER
  cmake -S . -B build \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DCMAKE_BUILD_TYPE=Release \
          -GNinja
  cmake --build build/ --config Release --verbose --parallel
  cmake --install build/ --config Release
popd

echo "-- Build SDL2_mixer"
pushd $MANYLINUX__SDL2_MIXER__FOLDER
  ./external/download.sh;
  cmake -B build -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
          -DCMAKE_BUILD_TYPE=Release \
          -DSDL2MIXER_MOD_MODPLUG=ON \
          -DSDL2MIXER_MOD_MODPLUG_SHARED=OFF \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DSDL2MIXER_VENDORED=ON \
          -GNinja
  cmake --build build/ --config Release --parallel --verbose
  cmake --install build/ --config Release
popd

echo "-- Build SDL2_image"
pushd $MANYLINUX__SDL2_IMAGE__FOLDER
  ./external/download.sh;
  # If KIVY_CROSS_PLATFORM is set to rpi, we need to build libwebp version 1.2.4,
  # as previous versions have issues with NEON and ARMv7.
  if [ "$KIVY_CROSS_PLATFORM" = "rpi" ]; then
    pushd external/libwebp
      git checkout 1.2.4
    popd
  fi
  cmake -B build -DBUILD_SHARED_LIBS=ON \
          -DCMAKE_BUILD_TYPE=Release \
          -DSDL2IMAGE_TIF=ON \
          -DSDL2IMAGE_WEBP=ON \
          -DSDL2IMAGE_TIF_SHARED=OFF \
          -DSDL2IMAGE_WEBP_SHARED=OFF \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DSDL2IMAGE_VENDORED=ON -GNinja
  cmake --build build/ --config Release --parallel --verbose
  cmake --install build/ --config Release
popd

echo "-- Build SDL2_ttf"
pushd $MANYLINUX__SDL2_TTF__FOLDER
  cmake -B build-cmake \
          -DBUILD_SHARED_LIBS=ON \
          -DSDL2TTF_HARFBUZZ=ON \
          -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
          -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DSDL2TTF_VENDORED=ON -GNinja
  cmake --build build-cmake --config Release --verbose
  cmake --install build-cmake/ --config Release --verbose
popd

popd