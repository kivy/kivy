#!/bin/bash
set -e -x

download_cache_curl() {
  fname="$1"
  key="$2"
  url_prefix="$3"

  if [ ! -f $key/$fname ]; then
    if [ ! -d $key ]; then
      mkdir "$key"
    fi
    curl -O -L "$url_prefix/$fname"
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
  download_cache_curl "${SDL2}.tar.gz" "osx-cache" "https://github.com/libsdl-org/SDL/archive/refs/tags"
  download_cache_curl "${SDL2_MIXER}.tar.gz" "osx-cache" "https://github.com/libsdl-org/SDL_mixer/archive"
  download_cache_curl "${SDL2_IMAGE}.tar.gz" "osx-cache" "https://github.com/libsdl-org/SDL_image/archive"
  download_cache_curl "${SDL2_TTF}.tar.gz" "osx-cache" "https://github.com/libsdl-org/SDL_ttf/archive/refs/tags"

  echo "-- Build SDL2 (Universal)"
  tar -xvf "${SDL2}.tar.gz"
  mv "SDL-${SDL2}" "SDL"
  pushd "SDL"
  xcodebuild ONLY_ACTIVE_ARCH=NO -project Xcode/SDL/SDL.xcodeproj -target Framework -configuration Release
  popd

  echo "-- Copy SDL2.framework to /Library/Frameworks"
  sudo cp -r SDL/Xcode/SDL/build/Release/SDL2.framework /Library/Frameworks

  echo "-- Build SDL2_mixer (Universal)"
  tar -xvf "${SDL2_MIXER}.tar.gz"
  mv "SDL_mixer-${SDL2_MIXER}" "SDL_mixer"
  pushd "SDL_mixer"
  xcodebuild ONLY_ACTIVE_ARCH=NO \
          -project Xcode/SDL_mixer.xcodeproj -target Framework -configuration Release
  popd

  echo "-- Copy SDL2_mixer.framework to /Library/Frameworks"
  sudo cp -r SDL_mixer/Xcode/build/Release/SDL2_mixer.framework /Library/Frameworks

  echo "-- Build SDL2_image (Universal)"
  tar -xvf "${SDL2_IMAGE}.tar.gz"
  mv "SDL_image-${SDL2_IMAGE}" "SDL_image"
  pushd "SDL_image"
  xcodebuild ONLY_ACTIVE_ARCH=NO \
          -project Xcode/SDL_image.xcodeproj -target Framework -configuration Release
  popd

  echo "-- Copy SDL2_image.framework to /Library/Frameworks"
  sudo cp -r SDL_image/Xcode/build/Release/SDL2_image.framework /Library/Frameworks

  echo "-- Build SDL2_ttf (Universal)"
  tar -xvf "${SDL2_TTF}.tar.gz"
  mv "SDL_ttf-${SDL2_TTF}" "SDL_ttf"
  pushd "SDL_ttf"
  xcodebuild ONLY_ACTIVE_ARCH=NO \
          -project Xcode/SDL_ttf.xcodeproj -target Framework -configuration Release
  popd

  echo "-- Copy SDL2_ttf.framework to /Library/Frameworks"
  sudo cp -r SDL_ttf/Xcode/build/Release/SDL2_ttf.framework /Library/Frameworks

  popd
}

install_platypus() {
  download_cache_curl "platypus$PLATYPUS.zip" "osx-cache" "https://github.com/sveinbjornt/Platypus/releases/download/$PLATYPUS"

  unzip "platypus$PLATYPUS.zip"
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