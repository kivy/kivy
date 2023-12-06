set -e -x

# macOS SDL2
MACOS__SDL2__VERSION="2.28.5"
MACOS__SDL2__URL="https://github.com/libsdl-org/SDL/releases/download/release-$MACOS__SDL2__VERSION/SDL2-$MACOS__SDL2__VERSION.tar.gz"
MACOS__SDL2__FOLDER="SDL2-${MACOS__SDL2__VERSION}"

# macOS SDL2_image
MACOS__SDL2_IMAGE__VERSION="2.8.0"
MACOS__SDL2_IMAGE__URL="https://github.com/libsdl-org/SDL_image/releases/download/release-$MACOS__SDL2_IMAGE__VERSION/SDL2_image-$MACOS__SDL2_IMAGE__VERSION.tar.gz"
MACOS__SDL2_IMAGE__FOLDER="SDL2_image-${MACOS__SDL2_IMAGE__VERSION}"

# macOS SDL2_mixer
MACOS__SDL2_MIXER__VERSION="2.6.3"
MACOS__SDL2_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/releases/download/release-$MACOS__SDL2_MIXER__VERSION/SDL2_mixer-$MACOS__SDL2_MIXER__VERSION.tar.gz"
MACOS__SDL2_MIXER__FOLDER="SDL2_mixer-${MACOS__SDL2_MIXER__VERSION}"

# macOS SDL2_ttf
MACOS__SDL2_TTF__VERSION="2.20.2"
MACOS__SDL2_TTF__URL="https://github.com/libsdl-org/SDL_ttf/releases/download/release-$MACOS__SDL2_TTF__VERSION/SDL2_ttf-$MACOS__SDL2_TTF__VERSION.tar.gz"
MACOS__SDL2_TTF__FOLDER="SDL2_ttf-${MACOS__SDL2_TTF__VERSION}"

# macOS libpng
MACOS__LIBPNG__VERSION="1.6.40"
MACOS__LIBPNG__URL="https://download.sourceforge.net/libpng/libpng16/${MACOS__LIBPNG__VERSION}/libpng-${MACOS__LIBPNG__VERSION}.tar.gz"
MACOS__LIBPNG__FOLDER="libpng-${MACOS__LIBPNG__VERSION}"

# Clean the dependencies folder
rm -rf kivy-dependencies

# Create the dependencies folder
mkdir kivy-dependencies

# Download the dependencies
echo "Downloading dependencies..."
mkdir kivy-dependencies/download
pushd kivy-dependencies/download
curl -L $MACOS__SDL2__URL -o "${MACOS__SDL2__FOLDER}.tar.gz"
curl -L $MACOS__SDL2_IMAGE__URL -o "${MACOS__SDL2_IMAGE__FOLDER}.tar.gz"
curl -L $MACOS__SDL2_MIXER__URL -o "${MACOS__SDL2_MIXER__FOLDER}.tar.gz"
curl -L $MACOS__SDL2_TTF__URL -o "${MACOS__SDL2_TTF__FOLDER}.tar.gz"
curl -L $MACOS__LIBPNG__URL -o "${MACOS__LIBPNG__FOLDER}.tar.gz"
popd

# Extract the dependencies into build folder
echo "Extracting dependencies..."
mkdir kivy-dependencies/build
pushd kivy-dependencies/build
tar -xzf ../download/${MACOS__SDL2__FOLDER}.tar.gz
tar -xzf ../download/${MACOS__SDL2_IMAGE__FOLDER}.tar.gz
tar -xzf ../download/${MACOS__SDL2_MIXER__FOLDER}.tar.gz
tar -xzf ../download/${MACOS__SDL2_TTF__FOLDER}.tar.gz
tar -xzf ../download/${MACOS__LIBPNG__FOLDER}.tar.gz
popd

# Create distribution folder
echo "Creating distribution folder..."
mkdir kivy-dependencies/dist
mkdir kivy-dependencies/dist/Frameworks

LIBPNG_SEARCH_PATH="$(pwd)/kivy-dependencies/dist/Frameworks/png.framework/Headers"
FRAMEWORK_SEARCH_PATHS="$(pwd)/kivy-dependencies/dist/Frameworks"

# Build the dependencies
pushd kivy-dependencies/build

# libpng is neeeded by SDL2_ttf to render emojis
echo "-- Build libpng (Universal)"
pushd $MACOS__LIBPNG__FOLDER
  cmake -S . -B build \
          -DCMAKE_INSTALL_PREFIX=../../dist \
          -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_OSX_ARCHITECTURES="x86_64;arm64" \
          -DPNG_TESTS=OFF \
          -DPNG_EXECUTABLES=OFF \
          -DPNG_SHARED=OFF \
          -DPNG_STATIC=OFF \
          -DPNG_FRAMEWORK=ON \
          -DCMAKE_C_FLAGS="-DPNG_ARM_NEON_OPT=0" \
          -GNinja
  cmake --build build/ --config Release --verbose --parallel
  cmake --install build/ --config Release

# for some reason, the framework is installed in lib instead of Frameworks
cp -r ../../dist/lib/png.framework ../../dist/Frameworks

popd

echo "-- Build SDL2 (Universal)"
pushd $MACOS__SDL2__FOLDER
xcodebuild ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=10.13 \
        -project Xcode/SDL/SDL.xcodeproj -target Framework -configuration Release
cp -r Xcode/SDL/build/Release/SDL2.framework ../../dist/Frameworks
popd

echo "-- Build SDL2_mixer (Universal)"
pushd $MACOS__SDL2_MIXER__FOLDER
xcodebuild ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=10.13 \
        -project Xcode/SDL_mixer.xcodeproj -target Framework -configuration Release
cp -r Xcode/build/Release/SDL2_mixer.framework ../../dist/Frameworks
popd

echo "-- Build SDL2_image (Universal)"
pushd $MACOS__SDL2_IMAGE__FOLDER
xcodebuild ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=10.13 \
        -project Xcode/SDL_image.xcodeproj -target Framework -configuration Release
cp -r Xcode/build/Release/SDL2_image.framework ../../dist/Frameworks
popd

echo "-- Build SDL2_ttf (Universal)"
pushd $MACOS__SDL2_TTF__FOLDER
xcodebuild ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=10.13 \
        -project Xcode/SDL_ttf.xcodeproj -target Framework -configuration Release \
        GCC_PREPROCESSOR_DEFINITIONS='$(GCC_PREPROCESSOR_DEFINITIONS) FT_CONFIG_OPTION_USE_PNG=1' \
        FRAMEWORK_SEARCH_PATHS='$(FRAMEWORK_SEARCH_PATHS) '"$FRAMEWORK_SEARCH_PATHS" \
        HEADER_SEARCH_PATHS='$(HEADER_SEARCH_PATHS) '"$LIBPNG_SEARCH_PATH" \
        OTHER_LDFLAGS='$(OTHER_LDFLAGS) -framework png'

cp -r Xcode/build/Release/SDL2_ttf.framework ../../dist/Frameworks
popd

popd