#!/bin/bash
set -e -x

# macOS SDL2
MACOS__SDL2__VERSION="2.24.0"
MACOS__SDL2__URL="https://github.com/libsdl-org/SDL/releases/download/release-$MACOS__SDL2__VERSION/SDL2-$MACOS__SDL2__VERSION.tar.gz"
MACOS__SDL2__FOLDER="SDL2-$MACOS__SDL2__VERSION"

# macOS SDL2_image
MACOS__SDL2_IMAGE__VERSION="2.6.2"
MACOS__SDL2_IMAGE__URL="https://github.com/libsdl-org/SDL_image/releases/download/release-$MACOS__SDL2_IMAGE__VERSION/SDL2_image-$MACOS__SDL2_IMAGE__VERSION.tar.gz"
MACOS__SDL2_IMAGE__FOLDER="SDL2_image-2.6.2"

# macOS SDL2_mixer
MACOS__SDL2_MIXER__VERSION="2.6.2"
MACOS__SDL2_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/releases/download/release-$MACOS__SDL2_MIXER__VERSION/SDL2_mixer-$MACOS__SDL2_MIXER__VERSION.tar.gz"
MACOS__SDL2_MIXER__FOLDER="SDL2_mixer-2.6.2"

# macOS SDL2_ttf
MACOS__SDL2_TTF__VERSION="2.20.1"
MACOS__SDL2_TTF__URL="https://github.com/libsdl-org/SDL_ttf/releases/download/release-$MACOS__SDL2_TTF__VERSION/SDL2_ttf-$MACOS__SDL2_TTF__VERSION.tar.gz"
MACOS__SDL2_TTF__FOLDER="SDL2_ttf-2.20.1"

# macOS Platypus version
MACOS__PLATYPUS__VERSION=5.3

download_cache_curl() {
  fname="$1"
  key="$2"
  url="$3"

  if [ ! -f $key/$fname ]; then
    if [ ! -d $key ]; then
      mkdir "$key"
    fi
    curl -L "$url" -o "$fname"
    cp "$fname" "$key"
  else
    cp "$key/$fname" .
  fi
}

arm64_set_path_and_python_version(){
  python_version="$1"
  if [[ $(/usr/bin/arch) = arm64 ]]; then
      export PATH=/opt/homebrew/bin:$PATH
      eval "$(pyenv init --path)"
      pyenv install $python_version -s
      pyenv global $python_version
      export PATH=$(pyenv prefix)/bin:$PATH
  fi
}

build_and_install_universal_kivy_sys_deps() {

  rm -rf deps_build
  mkdir deps_build

  pushd deps_build
  download_cache_curl "${MACOS__SDL2__FOLDER}.tar.gz" "osx-cache" $MACOS__SDL2__URL
  download_cache_curl "${MACOS__SDL2_MIXER__FOLDER}.tar.gz" "osx-cache" $MACOS__SDL2_MIXER__URL
  download_cache_curl "${MACOS__SDL2_IMAGE__FOLDER}.tar.gz" "osx-cache" $MACOS__SDL2_IMAGE__URL
  download_cache_curl "${MACOS__SDL2_TTF__FOLDER}.tar.gz" "osx-cache" $MACOS__SDL2_TTF__URL

  echo "-- Build SDL2 (Universal)"
  tar -xvf "${MACOS__SDL2__FOLDER}.tar.gz"
  pushd $MACOS__SDL2__FOLDER
  xcodebuild ONLY_ACTIVE_ARCH=NO -project Xcode/SDL/SDL.xcodeproj -target Framework -configuration Release
  echo "--- Copy SDL2.framework to /Library/Frameworks"
  sudo cp -r Xcode/SDL/build/Release/SDL2.framework /Library/Frameworks
  popd

  echo "-- Build SDL2_mixer (Universal)"
  tar -xvf "${MACOS__SDL2_MIXER__FOLDER}.tar.gz"
  pushd $MACOS__SDL2_MIXER__FOLDER
  xcodebuild ONLY_ACTIVE_ARCH=NO \
          -project Xcode/SDL_mixer.xcodeproj -target Framework -configuration Release
  echo "--- Copy SDL2_mixer.framework to /Library/Frameworks"
  sudo cp -r Xcode/build/Release/SDL2_mixer.framework /Library/Frameworks
  popd

  echo "-- Build SDL2_image (Universal)"
  tar -xvf "${MACOS__SDL2_IMAGE__FOLDER}.tar.gz"
  pushd $MACOS__SDL2_IMAGE__FOLDER
  xcodebuild ONLY_ACTIVE_ARCH=NO \
          -project Xcode/SDL_image.xcodeproj -target Framework -configuration Release
  echo "--- Copy SDL2_image.framework to /Library/Frameworks"
  sudo cp -r Xcode/build/Release/SDL2_image.framework /Library/Frameworks
  popd

  echo "-- Build SDL2_ttf (Universal)"
  tar -xvf "${MACOS__SDL2_TTF__FOLDER}.tar.gz"
  pushd $MACOS__SDL2_TTF__FOLDER
  xcodebuild ONLY_ACTIVE_ARCH=NO \
          -project Xcode/SDL_ttf.xcodeproj -target Framework -configuration Release
  echo "--- Copy SDL2_ttf.framework to /Library/Frameworks"
  sudo cp -r Xcode/build/Release/SDL2_ttf.framework /Library/Frameworks
  popd

  popd
}

install_platypus() {
  download_cache_curl "platypus$MACOS__PLATYPUS__VERSION.zip" "osx-cache" "https://github.com/sveinbjornt/Platypus/releases/download/$MACOS__PLATYPUS__VERSION/platypus$MACOS__PLATYPUS__VERSION.zip"

  unzip "platypus$MACOS__PLATYPUS__VERSION.zip"
  gunzip Platypus.app/Contents/Resources/platypus_clt.gz
  gunzip Platypus.app/Contents/Resources/ScriptExec.gz

  mkdir -p /usr/local/bin
  mkdir -p /usr/local/share/platypus
  cp Platypus.app/Contents/Resources/platypus_clt /usr/local/bin/platypus
  cp Platypus.app/Contents/Resources/ScriptExec /usr/local/share/platypus/ScriptExec
  cp -a Platypus.app/Contents/Resources/MainMenu.nib /usr/local/share/platypus/MainMenu.nib
  chmod -R 755 /usr/local/share/platypus
}

generate_osx_app_bundle() {
  py_version="$1"
  app_ver=$(PYTHONPATH=. KIVY_NO_CONSOLELOG=1 python3 -c 'import kivy; print(kivy.__version__)')

  cd ../
  git clone https://github.com/kivy/kivy-sdk-packager.git
  cd kivy-sdk-packager/osx

  ./create-osx-bundle.sh -k ../../kivy -p "$py_version" -v "$app_ver"
}

generate_osx_app_dmg_from_bundle() {
  pushd ../kivy-sdk-packager/osx
  ./create-osx-dmg.sh build/Kivy.app Kivy
  popd

  mkdir app

  mv ../kivy-sdk-packager/osx/Kivy.dmg "app/Kivy.dmg"
}

rename_osx_app() {
  py_version=${1:0:3}

  app_date=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y%m%d'))")
  git_tag=$(git rev-parse --short HEAD)
  app_ver=$(PYTHONPATH=. KIVY_NO_CONSOLELOG=1 python3 -c 'import kivy; print(kivy.__version__)')

  cp app/Kivy.dmg "app/Kivy-$app_ver-$git_tag-$app_date-python$py_version.dmg"
}

mount_osx_app() {
  pushd app
  hdiutil attach Kivy.dmg -mountroot .
  cp -R Kivy/Kivy.app Kivy.app
  popd
}

activate_osx_app_venv() {
  pushd app/Kivy.app/Contents/Resources/venv/bin
  source activate
  source kivy_activate
  popd
}