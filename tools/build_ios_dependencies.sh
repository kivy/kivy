set -e -x

# iOS SDL3
IOS__SDL3__VERSION="3.2.22"
IOS__SDL3__URL="https://github.com/libsdl-org/SDL/releases/download/release-$IOS__SDL3__VERSION/SDL3-$IOS__SDL3__VERSION.tar.gz"
IOS__SDL3__FOLDER="SDL3-$IOS__SDL3__VERSION"

# iOS SDL3_image
IOS__SDL3_IMAGE__VERSION="3.2.4"
IOS__SDL3_IMAGE__URL="https://github.com/libsdl-org/SDL_image/releases/download/release-$IOS__SDL3_IMAGE__VERSION/SDL3_image-$IOS__SDL3_IMAGE__VERSION.tar.gz"
IOS__SDL3_IMAGE__FOLDER="SDL3_image-$IOS__SDL3_IMAGE__VERSION"

# iOS SDL3_mixer
# IOS__SDL2_MIXER__VERSION="2.6.3"
# IOS__SDL2_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/releases/download/release-$IOS__SDL2_MIXER__VERSION/SDL2_mixer-$IOS__SDL2_MIXER__VERSION.tar.gz"
# IOS__SDL2_MIXER__FOLDER="SDL2_mixer-${IOS__SDL2_MIXER__VERSION}"
IOS__SDL3_MIXER__HASH="78a2035cf4cf95066d7d9e6208e99507376409a7"
IOS__SDL3_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/archive/$IOS__SDL3_MIXER__HASH.tar.gz"
IOS__SDL3_MIXER__FOLDER="SDL_mixer-$IOS__SDL3_MIXER__HASH"

# iOS SDL3_ttf
IOS__SDL3_TTF__VERSION="3.2.2"
IOS__SDL3_TTF__URL="https://github.com/libsdl-org/SDL_ttf/releases/download/release-$IOS__SDL3_TTF__VERSION/SDL3_ttf-$IOS__SDL3_TTF__VERSION.tar.gz"
IOS__SDL3_TTF__FOLDER="SDL3_ttf-$IOS__SDL3_TTF__VERSION"

IOS__ANGLE__VERSION="chromium-6943_rev1"
IOS__ANGLE_URL="https://github.com/kivy/angle-builder/releases/download/${IOS__ANGLE__VERSION}/angle-iphoneall-universal.tar.gz"
IOS__ANGLE__FOLDER="angle-iphoneall-universal"

# Clean the dependencies folder
rm -rf ios-kivy-dependencies

# Create the dependencies folder
mkdir ios-kivy-dependencies

# Download the dependencies
echo "Downloading dependencies..."
mkdir ios-kivy-dependencies/download
pushd ios-kivy-dependencies/download
curl -L $IOS__SDL3__URL -o "${IOS__SDL3__FOLDER}.tar.gz"
curl -L $IOS__SDL3_IMAGE__URL -o "${IOS__SDL3_IMAGE__FOLDER}.tar.gz"
curl -L $IOS__SDL3_MIXER__URL -o "${IOS__SDL3_MIXER__FOLDER}.tar.gz"
curl -L $IOS__SDL3_TTF__URL -o "${IOS__SDL3_TTF__FOLDER}.tar.gz"
curl -L $IOS__ANGLE_URL -o "${IOS__ANGLE__FOLDER}.tar.gz"
popd

# Extract the dependencies into build folder
echo "Extracting dependencies..."
mkdir ios-kivy-dependencies/build
pushd ios-kivy-dependencies/build
tar -xzf ../download/${IOS__SDL3__FOLDER}.tar.gz
tar -xzf ../download/${IOS__SDL3_IMAGE__FOLDER}.tar.gz
tar -xzf ../download/${IOS__SDL3_MIXER__FOLDER}.tar.gz
tar -xzf ../download/${IOS__SDL3_TTF__FOLDER}.tar.gz
popd

# Create distribution folder
echo "Creating distribution folder..."
mkdir ios-kivy-dependencies/dist
mkdir ios-kivy-dependencies/dist/Frameworks
mkdir ios-kivy-dependencies/dist/include
mkdir ios-kivy-dependencies/dist/lib


# Extract ANGLE in distribution folder
echo "Extracting ANGLE..."
pushd ios-kivy-dependencies/dist
mkdir $IOS__ANGLE__FOLDER
tar -xzf ../download/${IOS__ANGLE__FOLDER}.tar.gz -C $IOS__ANGLE__FOLDER
cp -a ${IOS__ANGLE__FOLDER}/include/* include
cp -r ${IOS__ANGLE__FOLDER}/*.xcframework Frameworks
rm -r $IOS__ANGLE__FOLDER
popd

# Build the dependencies
pushd ios-kivy-dependencies/build

echo "-- Build SDL3 (Universal)"
pushd $IOS__SDL3__FOLDER
for platform in "iOS" "iOS Simulator"; do
    platform_arg=$([ "$platform" = "iOS" ] && echo "iphoneos" || echo "iphonesimulator")
    xcodebuild archive -scheme SDL3 -project Xcode/SDL/SDL.xcodeproj \
        -archivePath "Xcode/SDL/build/Release-${platform_arg}" \
        -destination "generic/platform=${platform}" -configuration Release \
        "BUILD_LIBRARY_FOR_DISTRIBUTION=YES" "SKIP_INSTALL=NO"
done
xcodebuild -create-xcframework \
    -framework Xcode/SDL/build/Release-iphoneos.xcarchive/Products/Library/Frameworks/SDL3.framework \
    -framework Xcode/SDL/build/Release-iphonesimulator.xcarchive/Products/Library/Frameworks/SDL3.framework \
    -output ../../dist/Frameworks/SDL3.xcframework

# Copy SDL3 headers to distribution folder
mkdir -p ../../dist/include/SDL3
cp -a Xcode/SDL/build/Release-iphoneos.xcarchive/Products/Library/Frameworks/SDL3.framework/Headers/* ../../dist/include/SDL3

popd

echo "-- Build SDL3_mixer (Universal)"
pushd $IOS__SDL3_MIXER__FOLDER
for platform in "iOS" "iOS Simulator"; do
    platform_arg=$([ "$platform" = "iOS" ] && echo "iphoneos" || echo "iphonesimulator")
    xcodebuild archive -scheme SDL3_mixer -project Xcode/SDL_mixer.xcodeproj \
        -archivePath "Xcode/SDL_mixer/build/Release-${platform_arg}" \
        -destination "generic/platform=${platform}" -configuration Release \
        "BUILD_LIBRARY_FOR_DISTRIBUTION=YES" "SKIP_INSTALL=NO"
done
xcodebuild -create-xcframework \
    -framework Xcode/SDL_mixer/build/Release-iphoneos.xcarchive/Products/Library/Frameworks/SDL3_mixer.framework \
    -framework Xcode/SDL_mixer/build/Release-iphonesimulator.xcarchive/Products/Library/Frameworks/SDL3_mixer.framework \
    -output ../../dist/Frameworks/SDL3_mixer.xcframework
popd

echo "-- Build SDL3_image (Universal)"
pushd $IOS__SDL3_IMAGE__FOLDER
for platform in "iOS" "iOS Simulator"; do
    platform_arg=$([ "$platform" = "iOS" ] && echo "iphoneos" || echo "iphonesimulator")
    xcodebuild archive -scheme SDL3_image -project Xcode/SDL_image.xcodeproj \
        -archivePath "Xcode/SDL_image/build/Release-${platform_arg}" \
        -destination "generic/platform=${platform}" -configuration Release \
        "BUILD_LIBRARY_FOR_DISTRIBUTION=YES" "SKIP_INSTALL=NO"
done
xcodebuild -create-xcframework \
    -framework Xcode/SDL_image/build/Release-iphoneos.xcarchive/Products/Library/Frameworks/SDL3_image.framework \
    -framework Xcode/SDL_image/build/Release-iphonesimulator.xcarchive/Products/Library/Frameworks/SDL3_image.framework \
    -output ../../dist/Frameworks/SDL3_image.xcframework
popd

echo "-- Build SDL3_ttf (Universal)"
pushd $IOS__SDL3_TTF__FOLDER
sh ./external/download.sh

for platform in "iOS" "iOS Simulator"; do
    platform_arg=$([ "$platform" = "iOS" ] && echo "iphoneos" || echo "iphonesimulator")
    xcodebuild archive -scheme SDL3_ttf -project Xcode/SDL_ttf.xcodeproj \
        -archivePath "Xcode/SDL_ttf/build/Release-${platform_arg}" \
        -destination "generic/platform=${platform}" -configuration Release \
        "BUILD_LIBRARY_FOR_DISTRIBUTION=YES" "SKIP_INSTALL=NO"
done
xcodebuild -create-xcframework \
    -framework Xcode/SDL_ttf/build/Release-iphoneos.xcarchive/Products/Library/Frameworks/SDL3_ttf.framework \
    -framework Xcode/SDL_ttf/build/Release-iphonesimulator.xcarchive/Products/Library/Frameworks/SDL3_ttf.framework \
    -output ../../dist/Frameworks/SDL3_ttf.xcframework
popd

popd
