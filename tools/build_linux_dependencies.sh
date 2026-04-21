#!/bin/bash
set -e -x

# manylinux SDL3
MANYLINUX__SDL3__VERSION="3.4.0"
MANYLINUX__SDL3__URL="https://github.com/libsdl-org/SDL/releases/download/release-$MANYLINUX__SDL3__VERSION/SDL3-$MANYLINUX__SDL3__VERSION.tar.gz"
MANYLINUX__SDL3__FOLDER="SDL3-$MANYLINUX__SDL3__VERSION"

# manylinux SDL3_image
MANYLINUX__SDL3_IMAGE__VERSION="3.2.6"
MANYLINUX__SDL3_IMAGE__URL="https://github.com/libsdl-org/SDL_image/releases/download/release-$MANYLINUX__SDL3_IMAGE__VERSION/SDL3_image-$MANYLINUX__SDL3_IMAGE__VERSION.tar.gz"
MANYLINUX__SDL3_IMAGE__FOLDER="SDL3_image-$MANYLINUX__SDL3_IMAGE__VERSION"

# manylinux SDL3_mixer
MANYLINUX__SDL3_MIXER__VERSION="3.2.0"
MANYLINUX__SDL3_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/releases/download/release-$MANYLINUX__SDL3_MIXER__VERSION/SDL3_mixer-$MANYLINUX__SDL3_MIXER__VERSION.tar.gz"
MANYLINUX__SDL3_MIXER__FOLDER="SDL3_mixer-$MANYLINUX__SDL3_MIXER__VERSION"

# manylinux SDL3_ttf
MANYLINUX__SDL3_TTF__VERSION="3.2.2"
MANYLINUX__SDL3_TTF__URL="https://github.com/libsdl-org/SDL_ttf/releases/download/release-$MANYLINUX__SDL3_TTF__VERSION/SDL3_ttf-$MANYLINUX__SDL3_TTF__VERSION.tar.gz"
MANYLINUX__SDL3_TTF__FOLDER="SDL3_ttf-$MANYLINUX__SDL3_TTF__VERSION"

# manylinux libpng
MANYLINUX__LIBPNG__VERSION="1.6.47"
MANYLINUX__LIBPNG__URL="https://downloads.sourceforge.net/project/libpng/libpng16/$MANYLINUX__LIBPNG__VERSION/libpng-$MANYLINUX__LIBPNG__VERSION.tar.gz"
MANYLINUX__LIBPNG__FOLDER="libpng-$MANYLINUX__LIBPNG__VERSION"

# Clean the dependencies folder
rm -rf kivy-dependencies

# Create the dependencies folder
mkdir kivy-dependencies

# Download the dependencies
echo "Downloading dependencies..."
mkdir kivy-dependencies/download
pushd kivy-dependencies/download
curl -L $MANYLINUX__SDL3__URL -o "${MANYLINUX__SDL3__FOLDER}.tar.gz"
curl -L $MANYLINUX__SDL3_IMAGE__URL -o "${MANYLINUX__SDL3_IMAGE__FOLDER}.tar.gz"
curl -L $MANYLINUX__SDL3_MIXER__URL -o "${MANYLINUX__SDL3_MIXER__FOLDER}.tar.gz"
curl -L $MANYLINUX__SDL3_TTF__URL -o "${MANYLINUX__SDL3_TTF__FOLDER}.tar.gz"
curl -L $MANYLINUX__LIBPNG__URL -o "${MANYLINUX__LIBPNG__FOLDER}.tar.gz"
popd

# Extract the dependencies into build folder
echo "Extracting dependencies..."
mkdir kivy-dependencies/build
pushd kivy-dependencies/build
tar -xzf ../download/${MANYLINUX__SDL3__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__SDL3_IMAGE__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__SDL3_MIXER__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__SDL3_TTF__FOLDER}.tar.gz
tar -xzf ../download/${MANYLINUX__LIBPNG__FOLDER}.tar.gz
popd

# Create distribution folder
echo "Creating distribution folder..."
mkdir kivy-dependencies/dist

# Build the dependencies
pushd kivy-dependencies/build

# Check if "python3" exists, otherwise use "python" as fallback (which is the case for manylinux)
if command -v python3 &> /dev/null; then
  PYTHON_EXECUTABLE=python3
else
  PYTHON_EXECUTABLE=python
fi 

IS_RPI=$($PYTHON_EXECUTABLE -c "import platform; print('1' if 'raspberrypi' in platform.uname() else '0')")
if [ "$(dpkg --print-architecture)" = "armhf" ]; then
  IS_ARMHF=1
else
  IS_ARMHF=0
fi

echo "-- Build SDL3"
pushd $MANYLINUX__SDL3__FOLDER
  cmake -S . -B build \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DCMAKE_BUILD_TYPE=Release \
          -GNinja
  cmake --build build/ --config Release --verbose --parallel
  cmake --install build/ --config Release
popd


echo "-- Build libpng"
pushd $MANYLINUX__LIBPNG__FOLDER
  cmake -S . -B build \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DCMAKE_BUILD_TYPE=Release \
          -DPNG_TESTS=OFF \
          -DPNG_EXECUTABLES=OFF \
          -GNinja
  cmake --build build/ --config Release --verbose --parallel
  cmake --install build/ --config Release
popd

echo "-- Build SDL3_mixer"
pushd $MANYLINUX__SDL3_MIXER__FOLDER
  ./external/download.sh;

  sdl_mixer_builds_args=(
    -DCMAKE_POSITION_INDEPENDENT_CODE="ON"
    -DCMAKE_BUILD_TYPE="Release"
    -DCMAKE_INSTALL_PREFIX="../../dist"
    -DSDLMIXER_VENDORED="ON"
    -DSDLMIXER_MP3_MPG123="OFF"
    -GNinja
  )

  # if platform is rpi or cross-compiling for rpi, we need to set additional flags
  if { [ "$IS_RPI" = "1" ] && [ "$IS_ARMHF" = "1" ]; } || [ "$KIVY_CROSS_PLATFORM" = "rpi" ]; then
    sdl_mixer_builds_args+=(-DCMAKE_C_FLAGS="-mfpu=neon-fp-armv8")
  fi

  cmake -B build "${sdl_mixer_builds_args[@]}"

  cmake --build build/ --config Release --parallel --verbose
  cmake --install build/ --config Release
popd

echo "-- Build SDL3_image"
pushd $MANYLINUX__SDL3_IMAGE__FOLDER
  ./external/download.sh;
  cmake -B build -DBUILD_SHARED_LIBS=ON \
          -DCMAKE_BUILD_TYPE=Release \
          -DSDLIMAGE_VENDORED=ON \
          -DSDLIMAGE_AVIF=OFF \
          -DCMAKE_INSTALL_PREFIX=../../dist -GNinja
  cmake --build build/ --config Release --parallel --verbose
  cmake --install build/ --config Release
popd

echo "-- Build SDL3_ttf"
pushd $MANYLINUX__SDL3_TTF__FOLDER
  ./external/download.sh;
  cmake -B build-cmake \
          -DBUILD_SHARED_LIBS=ON \
          -DSDLTTF_HARFBUZZ=ON \
          -DFT_DISABLE_PNG=OFF \
          -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
          -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DSDLTTF_VENDORED=ON -GNinja
  cmake --build build-cmake --config Release --verbose
  cmake --install build-cmake/ --config Release --verbose
popd

popd

echo "-- Build ThorVG (static)"
# ThorVG is statically linked into the ``kivy.lib.thorvg`` Cython
# wrapper (see ``setup.py::determine_thorvg_flags``), so it must be
# available at Kivy build time. The script below pins the ThorVG
# version and meson options in a single place shared by Linux, macOS
# and Windows CI; see ``tools/build_thorvg.sh`` for details.
bash "$(dirname "$0")/build_thorvg.sh"
