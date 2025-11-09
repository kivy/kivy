

FWS_DIR="$PWD/kivy/dist/Frameworks"
echo "Frameworks dir: $FWS_DIR"

pip install -i https://pypi.anaconda.org/kivyschool/simple kivy-sdl3-angle -t $FWS_DIR

for PLATFORM in ios-arm64 ios-arm64_x86_64-simulator
do
    SDL_FW="$FWS_DIR/SDL3.xcframework/$PLATFORM/SDL3.framework"
    cp -rf $SDL_FW/Headers $SDL_FW/Headers/SDL3
done


ANGLE_VERSION="chromium-7151_rev1"

#wget -O angle-iphoneall-universal.tar.gz "https://github.com/kivy/angle-builder/releases/download/$ANGLE_VERSION/angle-iphoneall-universal.tar.gz"
curl -LO "https://github.com/kivy/angle-builder/releases/download/$ANGLE_VERSION/angle-iphoneall-universal.tar.gz"
tar -xzvf angle-iphoneall-universal.tar.gz -C $FWS_DIR
