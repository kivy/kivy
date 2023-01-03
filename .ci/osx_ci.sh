#!/bin/bash
set -e -x

# macOS Platypus version
MACOS__PLATYPUS__VERSION=5.4.1

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

install_platypus() {
  download_cache_curl "platypus$MACOS__PLATYPUS__VERSION.zip" "osx-cache" "https://github.com/sveinbjornt/Platypus/releases/download/v$MACOS__PLATYPUS__VERSION/platypus$MACOS__PLATYPUS__VERSION.zip"

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
